#!/usr/bin/perl -w

#Requires Spreadsheed::ParseExcel       http://search.cpan.org/~kwitknr/Spreadsheet-ParseExcel-0.2603/ParseExcel.pm     INSTALL LAST
#Requires Crypt::RC4                    http://www.perl.org/CPAN/authors/id/S/SI/SIFUKURT/Crypt-RC4-2.02.tar.gz
#Requires Digest::Perl::MD5             http://www.perl.org/CPAN/authors/id/D/DE/DELTA/Digest-Perl-MD5-1.8.tar.gz
#Requires IO::Scalar                    http://search.cpan.org/~dskoll/IO-stringy-2.110/lib/IO/Scalar.pm
#Requires OLE::Storage_Lite             http://search.cpan.org/~jmcnamara/OLE-Storage_Lite-0.19/lib/OLE/Storage_Lite.pm

use strict;
use Switch;
use Spreadsheet::ParseExcel;

my $parser   = Spreadsheet::ParseExcel->new();
my $workbook = $parser->parse('EBISU_Strings_with_ID.xls');

if ( !defined $workbook ) {
    die $parser->error(), ".\n";
}

print "FILE  :", $workbook->{File} , "\n";
print "COUNT :", $workbook->{SheetCount} , "\n";
print "AUTHOR:", $workbook->{Author} , "\n";

open(my $arrFileHandle, ">:utf8", "EBISU_StringExport_Array.h") or die "EBISU_StringExport_Array.h $!";
open(my $enumFileHandle, ">:utf8", "EBISU_StringExport_Defines.h") or die "EBISU_StringExport_Defines.h $!";

# Print headers for Array file.
my $time = localtime(time);
print $arrFileHandle "// This file was auto-generated on: ", $time;
print $arrFileHandle "\n\n#ifndef __EBISU_STRINGEXPORT_ARRAY_H__\n";
print $arrFileHandle "#define __EBISU_STRINGEXPORT_ARRAY_H__\n";
print $arrFileHandle "NSString * const cKeyArray[] = {\n";

# Print header for Defines file
print $enumFileHandle "// This file was auto-generated on: ", $time;
print $enumFileHandle "\n\n#ifndef __EBISU_STRINGEXPORT_DEFINES_H__\n";
print $enumFileHandle "#define __EBISU_STRINGEXPORT_DEFINES_H__\n";
print $enumFileHandle "typedef enum {\n";


my @languages = ();
my @fileHandles = ();

my $worksheet = $workbook->{Worksheet}[0];
my $worksheetName = $worksheet->get_name();
   
print "--------- SHEET:", $worksheet->{Name}, "\n";

#grab the language names out of this worksheet, and initialize the plists
my ( $col_min, $col_max ) = $worksheet->col_range();
my ( $row_min, $row_max ) = $worksheet->row_range();

my $itt = 0;

for my $col ( $col_min .. $col_max ) {
    my $cell = $worksheet->get_cell( $row_min, $col );
   
   if( !defined($cell))
    {
    	print "Undefined cell at Row: ", $row_min, " Col: ", $col, "\n";	
    }
    
    my $val = $cell->value();
    if( $val && $val ne '' && $val ne 'String ID' && $val ne 'English Status' && $val ne 'Comments' && $val ne 'Max Length') {
        print "Initializing   = ", $val, "\n";

        $languages[$itt] = $val;

        my $fileName = "$val.plist";

        open($fileHandles[$itt], ">:utf8", $fileName) or die "$fileName: $!";
        
        my $handle = $fileHandles[$itt];
        print $handle "<?xml version='1.0' encoding='UTF-8'?><!DOCTYPE plist PUBLIC '-//Apple Computer//DTD PLIST 1.0//EN' 'http://www.apple.com/DTDs/PropertyList-1.0.dtd'><plist version='1.0'><dict>";

        $itt++;

    }
}

print "\n";


print "Parsing worksheet:   ", $worksheetName, "\n";

my $didUpdateArrayAndEnumFiles = 0;

for my $col ( $col_min .. $col_max ) {

    my $testCell = $worksheet->get_cell( $row_min, $col );
    my $colTitle = $testCell->value();
    if( $colTitle && $colTitle ne '' && $colTitle ne 'String ID' && $colTitle ne 'English Status' && $colTitle ne 'Comments' && $colTitle ne 'Max Length') {

        my $index = 0;
        print "Column Title: ", $colTitle, "\n";

        while($languages[$index] ne $colTitle) {
            #print "Language: ", $languages[$index], " ", $index, "\n";
            $index++;
        }


        my $fileHandle = $fileHandles[$index];

        for my $row ( ($row_min + 1) .. $row_max ) {

            my $keyCell = $worksheet->get_cell( $row, $col_min );  #keys must be in the leftmost column
            next unless $keyCell;
 
            my $valueCell = $worksheet->get_cell( $row, $col );
            next unless $valueCell;

            my $key = $keyCell->value();
            my $value = $valueCell->value();

            
            $value =~ s/</@/g;
            $value =~ s/>/@/g;

            if($key ne '') {
                print $fileHandle "<key>$key</key><string>$value</string>";

                
                if($didUpdateArrayAndEnumFiles == 0) {
                    #print to array and enum files
                    print $arrFileHandle "    [$key]          = @\"$key\",\n";
                    print $enumFileHandle "    $key,\n";
                }
                
            }
        }
        
        $didUpdateArrayAndEnumFiles = 1;
    }
}   

print $arrFileHandle "};";
print $arrFileHandle "\n#endif\n";

print $enumFileHandle "} eStringKey;";
print $enumFileHandle "\n#endif\n";

for my $handle ( @fileHandles ) {

    print $handle "</dict></plist>";
    close $handle;

}
