package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"net/textproto"
	"regexp"
	"strings"
	"time"
)

// Type for differentiate states if ADC connection.
type State int

// Different value of an ADC connection.
const (
	INITIAL State = iota
	PROTOCOL
	IDENTIFY
	VERIFY
	NORMAL
	DATA
)

// Message types
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

// Commands that we handle
const (
	STA = "STA"
	SUP = "SUP"
	SID = "SID"
	INF = "INF"
	MSG = "MSG"
	SCH = "SCH"
)

// Intermediate regex items for building the complex reMsg
const (
	PatternMsgType = "[" + MsgBroadcast + MsgClient + MsgDirect + MsgEcho + MsgFeature + MsgHub + MsgInfo + MsgUdp + "]"
	PatternCommand = STA + "|" + SUP + "|" + SID + "|" + INF + "|" + MSG + "|" + SCH
)

const HELP = `Available commands: $uptime`

var (
	// Overvall regex to parse each incoming command.
	reMsg = regexp.MustCompile(`^(?P<msgType>` + PatternMsgType + `)(?P<command>` + PatternCommand + `)\s(?P<args>.*)`)
	// Regex to parse the arguments per command.
	reArgsMap = map[string]*regexp.Regexp{
		STA: regexp.MustCompile(`^(?P<severity>\d)(?P<errorCode>\d{2})\s(?P<description>.*)$`),
		SUP: regexp.MustCompile(`^(?P<keyvalues>.*)$`),
		SID: regexp.MustCompile(`^(?P<sid>\w{4})$`),
		INF: regexp.MustCompile(`^((?P<sid>[A-Z]{4})\s)?(?P<keyvalues>.*)$`),
		MSG: regexp.MustCompile(`^(?P<sid>[A-Z]{4})\s(?P<text>.*)$`),
	}
	// Some commands contain key value pairs. Thats the regex to parse them.
	reKeyValueMap = map[string]*regexp.Regexp{
		SUP: regexp.MustCompile(`(?P<value>AD|RM)(?P<key>\w*)`),
		INF: regexp.MustCompile(`(?P<key>\w{2})(?P<value>[^ ]*)`),
	}
	// Information data send to hub and other clients
	inf = map[string]string{
		"ID": "SXX4RUEEB263P3EX7VAGSMHGO4XVDBTQOJZNONI",
		"PD": "4MH2IBPDTOP34ELXWSXRY35CSTHDR3PCOMWZPMI",
		"CT": "1",
		"NI": "nusbot",
		"VE": escape("nusbot/0.2.0"),
		"DE": escape("I am a bot, type $help into the chat"),
		"SU": "TCP4",
	}
)

// Formatted version of the INF map for sending over the wire.
func formattedInf() string {
	arr := make([]string, 0, len(inf))
	for key, value := range inf {
		arr = append(arr, key+value)
	}
	return strings.Join(arr, " ")
}

// Escapes a text according ADC.
func escape(text string) string {
	return strings.Replace(text, " ", `\s`, -1)
}

// Unescapes a text according ADC.
func unescape(text string) string {
	return strings.Replace(text, `\s`, " ", -1)
}

// Parses the string str with regex re and returns a map with the named group name as key and
// the matched value as value.
func parseArgs(re *regexp.Regexp, str string) map[string]string {
	args := make(map[string]string)

	if re == nil || str == "" {
		return args
	}

	submatches := re.FindStringSubmatch(str)

	if submatches == nil {
		return args
	}

	for index, name := range re.SubexpNames() {
		if index == 0 || name == "" {
			continue
		}
		args[name] = submatches[index]
	}

	return args
}

// Parses a given string using the given regexp with named groups "key" and "value". A map is returned
// with the value of named group "key" as key and value of "value" as value :)
func parseKeyValues(re *regexp.Regexp, str string) map[string]string {
	keyvalues := make(map[string]string)

	if re == nil || str == "" {
		return keyvalues
	}

	submatches := re.FindAllStringSubmatch(str, -1)
	keyFirst := re.SubexpNames()[1] == "key"

	for _, submatch := range submatches {
		if keyFirst {
			keyvalues[submatch[1]] = submatch[2]
		} else {
			keyvalues[submatch[2]] = submatch[1]
		}
	}
	return keyvalues
}

// Data structure with all information about the hub or client ADC connection.
type AdcConnection struct {
	target  string
	conn    net.Conn
	inf     map[string]string
	state   State
	sid     string
	users   map[string]*AdcConnection
	started time.Time
}

// Creates a new AdcConnection instance.
func NewAdcConnection(target string) *AdcConnection {
	return &AdcConnection{
		target:  target,
		inf:     make(map[string]string),
		state:   PROTOCOL,
		users:   make(map[string]*AdcConnection),
		started: time.Now(),
	}
}

// Entrypoint that starts a connection to the target and it's running the event loop.
// Parses each incoming command and calls Handle() with parsed data.
func (ac *AdcConnection) Run() {
	conn, err := net.Dial("tcp", ac.target)
	if err != nil {
		log.Fatal("Unable to connect to: ", ac.target, err)
	}
	ac.conn = conn
	log.Printf("Connected to %s", ac.conn.RemoteAddr())
	defer conn.Close()

	fmt.Fprintln(conn, MsgHub+SUP, "ADBASE", "ADTIGR")
	tp := textproto.NewReader(bufio.NewReader(ac.conn))
	for {
		line, err := tp.ReadLine()
		if err != nil {
			log.Fatal("Can not read from connection", err)
		}
		if match := parseArgs(reMsg, line); match != nil {
			msgType := match["msgType"]
			command := match["command"]
			args := parseArgs(reArgsMap[command], match["args"])
			keyvalues := parseKeyValues(reKeyValueMap[command], args["keyvalues"])
			delete(args, "keyvalues")
			ac.Handle(msgType, command, args, keyvalues)
		} else {
			log.Println("Ignoring unknown command:", line)
		}
	}
}

// Here's the place for the logic.
func (ac *AdcConnection) Handle(msgType string, cmd string, args map[string]string, keyvalues map[string]string) {
	switch cmd {
	case STA:
		if args["severity"] == "0" {
			log.Println("INFO:", unescape(args["description"]))
		} else {
			log.Fatalf("Error %s received from hub: %s", args["errorCode"], unescape(args["description"]))
		}
	case SID:
		if ac.state == PROTOCOL {
			ac.state = IDENTIFY
			ac.sid = args["sid"]
			log.Println("Got Session ID:", ac.sid)
		}
	case INF:
		// Determine where to store this information
		var updateTarget map[string]string
		if msgType == MsgInfo && args["sid"] == "" { // it's a hub
			updateTarget = ac.inf
			if ac.state == IDENTIFY {
				ac.state = NORMAL
				fmt.Fprintln(ac.conn, MsgBroadcast+INF, ac.sid, formattedInf())
			}
		} else { // user inf
			user, ok := ac.users[args["sid"]]
			if !ok {
				user = NewAdcConnection("")
				ac.users[args["sid"]] = user
			}
			updateTarget = user.inf
		}
		// Update values
		for key, value := range keyvalues {
			updateTarget[key] = value
		}
	case MSG:
		if args["sid"] == ac.sid { // ignore own msgs echoed back
			break
		}
		switch args["text"] {
		case "$help":
			fmt.Fprintln(ac.conn, MsgBroadcast+MSG, ac.sid, escape(HELP))
		case "$uptime":
			fmt.Fprintln(ac.conn, MsgBroadcast+MSG, ac.sid, escape(fmt.Sprintf("Running since %s", time.Since(ac.started))))
		}
	case SUP:
	case SCH:
	default:
		fmt.Println(msgType, cmd, args, keyvalues)
	}
}

func main() {
	hub := NewAdcConnection("10.10.0.1:1511")
	hub.Run()
}
