"""
2019-04-30

This script reads a molecule file generated by CAMPAREE, counts the number of
occurrences of each transcript, and generated a FASTA file of these sequences,
as well as a table of counts for each molecule. Note, this version of the script
is designed to work with a molecule file that just contains mature mRNA sequences
and completely unspliced pre-mRNA (contain all introns). It might still work with
molecule files that contain molecule-specific edits or splicing events, but it
was not designed to work specifically in this scenario.

"""

import argparse
import sys
import os
import re

class MoleculeFileToFastaAndCountTable():

    """
    Formatted strings for each output file.
    """
    _output_fasta_pattern = ('{prefix}transcriptome{parental_suffix}.fa')
    _output_count_table_pattern = ('{prefix}count_table{parental_suffix}.txt')

    def __init__(self, molecule_file, output_directory):

        if not os.path.isdir(output_directory):
            raise(f"The following output directory does not exist:\n{output_directory}")
        if not os.path.isfile(molecule_file):
            raise(f"The following molecule file does not exist:\n{molecule_file}")

        self.molecule_file = molecule_file
        self.output_directory = output_directory
        self.parental_suffix_list = ['_1', '_2']

    def execute(self, output_prefix="", separate_by_parent=False):

        """
        Track various aspects of molecules in the molecule file by source transcript ID.
        """
        counts_by_transcript = dict()
        sequences_by_transcript = dict()
        fasta_headers_by_transcript = dict()

        with open(self.molecule_file, 'r') as input_molecule_file:
            #Skip header line
            input_header = next(input_molecule_file)

            for molecule in input_molecule_file:
                molecule_data = molecule.rstrip().split("\t")
                transcript_id = molecule_data[0]
                transcript_seq = molecule_data[5]

                if not counts_by_transcript.get(transcript_id, None):
                    counts_by_transcript[transcript_id] = 1
                    sequences_by_transcript[transcript_id] = transcript_seq
                    fasta_headers_by_transcript[transcript_id] = f">{transcript_id} {' '.join(molecule_data[1:5])}"
                else:
                    counts_by_transcript[transcript_id] += 1

        sorted_transcript_ids = sorted(counts_by_transcript.keys())
        '''
        The filenames are stored in lists so they can expand if the user is opts
        to output separate files for each parental transcriptome.
        '''
        output_fasta_filename = [os.path.join(self.output_directory,
                                              self._output_fasta_pattern.format(prefix=output_prefix,
                                                                                parental_suffix=""))]
        output_count_filename = [os.path.join(self.output_directory,
                                              self._output_count_table_pattern.format(prefix=output_prefix,
                                                                                      parental_suffix=""))]

        if separate_by_parent:
            # Update output filenames so there are separate ones for each parent.
            output_fasta_filename = [os.path.join(self.output_directory,
                                                  self._output_fasta_pattern.format(prefix=output_prefix,
                                                                                    parental_suffix=suffix)) \
                                     for suffix in self.parental_suffix_list]
            output_count_filename = [os.path.join(self.output_directory,
                                                  self._output_count_table_pattern.format(prefix=output_prefix,
                                                                                          parental_suffix=suffix)) \
                                     for suffix in self.parental_suffix_list]

        '''
        Generate output file(s). For loop will run once if user opted to print
        output from both parents together and twice if user opted for separate
        output by parent.
        '''
        # TODO: There's probably a way to generalize all of the code here to
        #       work with an arbitrary number of parental genomes (probably
        #       using something like contextlib.ExitStack) while only performing
        #       a single pass on sorted_transcript_ids, rather than parsing the
        #       whole thing for each parental genome file.
        for output_file_num in range(len(output_fasta_filename)):

            # Regex for identifying and parsing transcript IDs.
            parent_id_pattern = (r'([a-zA-Z0-9]+){parental_suffix}(_pre_mRNA)?')
            transcript_id_by_parent_regex = \
                re.compile(parent_id_pattern.format(parental_suffix=self.parental_suffix_list[output_file_num]))

            with open(output_fasta_filename[output_file_num], mode='w') as fasta_file, \
                 open(output_count_filename[output_file_num], mode='w') as count_file:

                #Print header line for count table
                count_file.write("Transcript_ID\tCount\n")

                for transcript_id in sorted_transcript_ids:
                    if not separate_by_parent or \
                       (separate_by_parent and transcript_id_by_parent_regex.match(transcript_id)):
                        count_file.write(f"{transcript_id}\t{counts_by_transcript[transcript_id]}\n")
                        fasta_file.write(fasta_headers_by_transcript[transcript_id] + "\n")
                        fasta_file.write(sequences_by_transcript[transcript_id] + "\n")

    @staticmethod
    def main():
        """Entry point into script when called directly.

        Parses arguments, gathers input and output filenames, and calls methods
        that perform the actual operation.

        """
        parser = argparse.ArgumentParser(description='Create transcriptome FASTA and'
                                                     ' count table from a CAMPAREE molecule file')
        parser.add_argument('-i', '--input_molecule_file', required=True,
                            help="Path to the molecule file.")
        parser.add_argument('-o', '--output_directory', required=True,
                            help="Path to output directory. FASTA and count table"
                                 " will be saved here.")
        parser.add_argument('-p', '--output_prefix', required=False, default="",
                            help="Prefix to add to all output files.")
        parser.add_argument('-s', '--separate_by_parent', action='store_true',
                            help="Generate separate FASTA and count table files for"
                                 " molecules from each parental genome. Assumes transcript"
                                 " IDs in molecule file have _1/_2 suffixes to identify the"
                                 " source parent.")

        args = parser.parse_args()

        molecule_file_converter = MoleculeFileToFastaAndCountTable(molecule_file=args.input_molecule_file,
                                                                   output_directory=args.output_directory)
        molecule_file_converter.execute(output_prefix=args.output_prefix,
                                        separate_by_parent=args.separate_by_parent)

if __name__ == '__main__':
    sys.exit(MoleculeFileToFastaAndCountTable.main())
