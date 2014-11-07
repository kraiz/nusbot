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

type HubState int

const (
	INITIAL HubState = iota
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

type Bot struct {
	server string
	nick   string
	conn   net.Conn
	state  HubState
	sid    string
}

func (bot *Bot) Run() {
	conn, err := net.Dial("tcp", bot.server)
	if err != nil {
		log.Fatal("Unable to connect to hub %s", bot.server, err)
	}
	bot.conn = conn
	log.Printf("Connected to %s", bot.conn.RemoteAddr())
	defer conn.Close()

	fmt.Fprintln(conn, "HSUP ADBASE ADTIGR")
	tp := textproto.NewReader(bufio.NewReader(bot.conn))
	for {
		line, err := tp.ReadLine()
		if err != nil {
			log.Fatal("Can not read from connection", err)
		}

		if match := parse(reMsg, line); match != nil {
			bot.Handle(match["msgType"], match["command"], parse(reArgsMap[match["command"]], match["args"]))
		} else {
			log.Println("Ignoring unknown command:", line)
		}
	}
}

func (bot *Bot) Handle(msgType string, cmd string, args map[string]string) {
	switch cmd {
	case STA:
		if args["severity"] == "0" {
			log.Println("INFO:", unescape(args["description"]))
		} else {
			log.Fatalf("Error %s received from hub: %s", args["errorCode"], unescape(args["description"]))
		}
	case SUP:
		if bot.state == INITIAL {
			bot.state = PROTOCOL
		}
	case SID:
		bot.sid = args["sid"]
		log.Println("Got Session ID:", bot.sid)
	default:
		fmt.Println(msgType, cmd, args)
	}
}

func main() {
	bot := &Bot{server: "10.10.0.1:1511", nick: "nusbot2"}
	bot.Run()
}
