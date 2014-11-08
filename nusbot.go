package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"net/textproto"
	"regexp"
	"strings"
)

type State int

const (
	INITIAL State = iota
	PROTOCOL
	IDENTIFY
	VERIFY
	NORMAL
	DATA
)

const (
	MsgBroadcast = "B"
	MsgClient    = "C"
	MsgDirect    = "D"
	MsgEcho      = "E"
	MsgFeature   = "F"
	MsgHub       = "H"
	MsgInfo      = "I"
	MsgUdp       = "U"
)

const (
	STA = "STA"
	SUP = "SUP"
	SID = "SID"
)

const (
	PatternMsgType = "[" + MsgBroadcast + MsgClient + MsgDirect + MsgEcho + MsgFeature + MsgHub + MsgInfo + MsgUdp + "]"
	PatternCommand = STA + "|" + SUP + "|" + SID
)

var reMsg = regexp.MustCompile(`^(?P<msgType>` + PatternMsgType + `)(?P<command>` + PatternCommand + `)\s(?P<args>.*)`)
var reArgsMap = map[string]*regexp.Regexp{
	STA: regexp.MustCompile(`^(?P<severity>\d)(?P<errorCode>\d{2})\s(?P<description>.*)$`),
	SUP: regexp.MustCompile(`(AD|RM)(\w*)`),
	SID: regexp.MustCompile(`^(?P<sid>\w{4})$`),
}

// helpers
func escape(text string) string {
	return strings.Replace(text, " ", `\s`, -1)
}

func unescape(text string) string {
	return strings.Replace(text, `\s`, " ", -1)
}

func parse(re *regexp.Regexp, str string) map[string]string {
	submatchMap := make(map[string]string)
	submatches := re.FindStringSubmatch(str)

	if submatches == nil {
		return nil
	}

	for index, name := range re.SubexpNames() {
		if index == 0 || name == "" {
			continue
		}
		submatchMap[name] = submatches[index]
	}

	return submatchMap
}

type AdcConnection struct {
	target string
	conn   net.Conn
	inf    map[string]string
	state  State
	sid    string
}

func (ac *AdcConnection) Run() {
	conn, err := net.Dial("tcp", ac.target)
	if err != nil {
		log.Fatal("Unable to connect to: ", ac.target, err)
	}
	ac.conn = conn
	log.Printf("Connected to %s", ac.conn.RemoteAddr())
	defer conn.Close()

	fmt.Fprintln(conn, "HSUP ADBASE ADTIGR")
	tp := textproto.NewReader(bufio.NewReader(ac.conn))
	for {
		line, err := tp.ReadLine()
		if err != nil {
			log.Fatal("Can not read from connection", err)
		}

		if match := parse(reMsg, line); match != nil {
			ac.Handle(match["msgType"], match["command"], parse(reArgsMap[match["command"]], match["args"]))
		} else {
			log.Println("Ignoring unknown command:", line)
		}
	}
}

func (ac *AdcConnection) Handle(msgType string, cmd string, args map[string]string) {
	switch cmd {
	case STA:
		if args["severity"] == "0" {
			log.Println("INFO:", unescape(args["description"]))
		} else {
			log.Fatalf("Error %s received from hub: %s", args["errorCode"], unescape(args["description"]))
		}
	case SUP:
		if ac.state == INITIAL {
			ac.state = PROTOCOL
		}
	case SID:
		ac.sid = args["sid"]
		log.Println("Got Session ID:", ac.sid)
	default:
		fmt.Println(msgType, cmd, args)
	}
}

func main() {
	hub := &AdcConnection{target: "10.10.0.1:1511"}
	hub.Run()
}
