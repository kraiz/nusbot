package adc

import "encoding/xml"

func ParseFilelist(data []byte) (*FileListing, error) {
	var filelist FileListing
	err := xml.Unmarshal(data, &filelist)
	return &filelist, err
}

type FileListing struct {
	XMLName   xml.Name `xml:"FileListing"`
	Version   int      `xml:"Version,attr"`
	CID       string   `xml:"CID,attr"`
	Base      string   `xml:"Base,attr"`
	Generator string   `xml:"Generator,attr"`
	Children  []Node   `xml:"Directory"`
}

type Node interface {
	Name() strin""g
	Size() int64
}

type File struct {
	XMLName xml.Name `xml:"File"`
	name    string
	size    int64
	tth     string
}

type Directory struct {
	XMLName  xml.Name `xml:"Directory"`
	name     string   `xml:"Name,attr"`
	children []Node
}

func (f *File) Name() string {
	return f.name
}

func (f *File) Size() int64 {
	return f.size
}
func (f *Directory) Name() string {
	return f.name
}

func (f *Directory) Size() int64 {
	var size int64 = 0
	for _, childNode := range f.children {
		size += childNode.Size()
	}
	return size
}
