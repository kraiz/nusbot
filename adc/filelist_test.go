package adc

import (
	"log"
	"testing"
)

var data = []byte(`
		<?xml version="1.0" encoding="utf-8" standalone="yes"?>
		<FileListing Version="1" CID="PYCOXCNHVPMZVE34V3O7B4PAK436DRWYQX5JT2Q" Base="/" Generator="EiskaltDC++ 2.3.0">
			<Directory Name="A">
				<Directory Name="AA">
					<File Name="AA_1" Size="47548918" TTH="R33WPWXMUVGLY5L6HIMNGO67PXBHOSLGZQU5S4Q"/>
					<File Name="AA_2" Size="306661410" TTH="4WLR4HDOQOYKLLMANSHHVOSHSWDW3SUBOCJNGFY"/>
				</Directory>
				<Directory Name="AB">
					<File Name="AB_1" Size="160061125" TTH="KOKX637HXCZAFK4ASA7Z7HOO2YE2WTWC6RLVDGA"/>
					<File Name="AB_2" Size="20489777" TTH="KUZSMOOEQQ3BYGWTJZR2FMPY2H34HAON6BN6TRI"/>
				</Directory>
				<Directory Name="AC">
					<File Name="AC_1" Size="562574624" TTH="O5VYHOHXZZLUWZEUJ6W6NMBIECGNB3F2QE2GRDY"/>
					<File Name="AC_2" Size="114847320" TTH="WHA4RGWOJASQJE24OL2DV4NFDA3MG7E2MSFE4CI"/>
					<File Name="AC_3" Size="41244818" TTH="6ZA3KCRTZIYS2DMAZR4MRE2IJB42CTFAEL4MZYY"/>
					<File Name="AC_4" Size="10366740" TTH="MUPLQQXITDWT6WFK77TATAOEQBCQGM3EJY27PGA"/>
					<File Name="AC_5" Size="32695711" TTH="5ZMHTRVNNDB5HAD2UXNQDOW5IKIYY2Z7GROYALY"/>
					<File Name="AC_6" Size="23351211" TTH="6VXVE4FP5IGBUMZDBDT5Z73INULKWVRBY6Y24NA"/>
				</Directory>
			</Directory>
			<Directory Name="B">
				<Directory Name="BA">
					<File Name="BA_1" Size="47548918" TTH="R33WPWXMUVGLY5L6HIMNGO67PXBHOSLGZQU5S4Q"/>
					<File Name="BA_2" Size="306661410" TTH="4WLR4HDOQOYKLLMANSHHVOSHSWDW3SUBOCJNGFY"/>
				</Directory>
			</Directory>
		</FileListing>
	`)

func TestParseFilelist(t *testing.T) {
	filelist, err := ParseFilelist(data)
	if err != nil {
		t.Error("Error parsing filelist", err)
	}
	log.Println(filelist)
}
