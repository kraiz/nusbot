package nusbot

import (
	"fmt"
	"time"

	"github.com/kraiz/nusbot/adc"
)

type Nusbot struct {
	hub *adc.AdcConnection
}

func NewNusbot(hub string) *Nusbot {
	return &Nusbot{
		hub: adc.NewAdcConnection(hub),
	}
}

func (nb *Nusbot) Run() {
	go nb.Handle()
	nb.hub.Run()
}

func (nb *Nusbot) Handle() {
	for {
		select {
		case <-nb.hub.CConnected:

			fmt.Println("CONNECTED")
		case msg := <-nb.hub.CMsg:
			switch msg {
			case "$help":
				nb.hub.ChatSay(`Available commands: $uptime`)
			case "$uptime":
				nb.hub.ChatSay("Running since %s", time.Since(nb.hub.Started))
			}
		}
	}
}

func (nb *Nusbot) newFileList(nick string, filelist string) {

}
