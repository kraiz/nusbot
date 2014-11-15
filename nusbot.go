package nusbot

import (
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
	nb.hub.Run()
}

func (nb *Nusbot) Handle() {
	for {
		select {
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
