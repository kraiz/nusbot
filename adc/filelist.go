package adc

import (
	"encoding/xml"
	"time"
)

type FileListing struct {
	XMLName     xml.Name    `xml:"FileListing"`
	Version     int         `xml:"Version,attr"`
	CID         string      `xml:"CID,attr"`
	Base        string      `xml:"Base,attr"`
	Generator   string      `xml:"Generator,attr"`
	Directories []Directory `xml:"Directory"`
}

type Directory struct {
	XMLName     xml.Name    `xml:"Directory"`
	Name        string      `xml:"Name,attr"`
	Directories []Directory `xml:"Directory"`
	Files       []File      `xml:"File"`
}

type File struct {
	XMLName xml.Name `xml:"File"`
	Name    string   `xml:"Name,attr"`
	TTH     string   `xml:"TTH,attr"`
	Size    uint64   `xml:"Size,attr"`
}

type Changelist struct {
	CID       string
	Nickname  string
	FirstSeen string
	LastScan  int64
	Changes   []Change
}

type Change struct {
	Time    time.Time
	Added   []string
	Removed []string
}

func (dir *Directory) CalcSize() uint64 {
	var size uint64 = 0
	for _, subDirectory := range dir.Directories {
		size += subDirectory.CalcSize()
	}
	for _, subFile := range dir.Files {
		size += subFile.Size
	}
	return size
}

func (dir *Directory) Diff(dir2 *Directory) ([]string, []string) {
	// TODO
}

func (fl *FileListing) Diff(fl2 *FileListing) *Change {
	// TODO
}

func ParseFilelist(data []byte) (*FileListing, error) {
	var filelist FileListing
	err := xml.Unmarshal(data, &filelist)
	return &filelist, err
}
