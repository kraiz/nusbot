package adc

type Node interface {
	Name() string
	Size() int64
}

type File struct {
	name string
	size int64
	tth  string
}

func (f *File) Name() string {
	return f.name
}

func (f *File) Size() int64 {
	return f.size
}

type Directory struct {
	name     string
	children []Node
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
