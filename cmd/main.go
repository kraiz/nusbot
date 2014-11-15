package main

import (
	"flag"

	"github.com/kraiz/nusbot"
)

var hub = flag.String("hub", "10.10.0.1:1511", "hub address in format <ip>:<port>")

func main() {
	bot := nusbot.NewNusbot(*hub)
	bot.Run()
}
