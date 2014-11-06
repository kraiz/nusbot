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
)

const (
	PatternMsgType = "[" + MsgBroadcast + MsgClient + MsgDirect + MsgEcho + MsgFeature + MsgHub + MsgInfo + MsgUdp + "]"
	PatternCommand = STA
	PatternSTA     = `^(?P<severity>\d)(?P<error_code>\d{2})\s(?P<text>.*)$`
)

var patternMsg = fmt.Sprintf(`^(%s)(%s)\s(.*)`, PatternMsgType, PatternCommand)
var reMsg = regexp.MustCompile(patternMsg)
var reSTA = regexp.MustCompile(PatternSTA)

func escape(text string) string {
	return strings.Replace(text, " ", `\s`, -1)
}

func unescape(text string) string {
	return strings.Replace(text, `\s`, " ", -1)
}

type Bot struct {
	server string
	nick   string
	conn   net.Conn
	state  HubState
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
		match := reMsg.FindStringSubmatch(line)
		if len(match) != 4 {
			log.Println("Ignoring unknown command:", line)
			continue
		}
		bot.Handle(match[1], match[2], match[3])
	}
}

func (bot *Bot) Handle(msgType string, cmd string, args string) {
	fmt.Println(msgType, cmd, args)

	switch cmd {
	case STA:
		match := reSTA.FindStringSubmatch(args)
		fmt.Println("jaaaaa", unescape(match[3]))
	}
}

func main() {
	fmt.Println(patternMsg)
	bot := &Bot{server: "10.10.0.1:1511", nick: "nusbot2"}
	bot.Run()
}
