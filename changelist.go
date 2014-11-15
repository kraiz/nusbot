package nusbot

import "time"

type Changelist struct {
	Id        string
	FirstSeen string
	LastScan  int64
	Changes   []Change
}

type Change struct {
	Time    time.Time
	Added   []string
	Removed []string
}
