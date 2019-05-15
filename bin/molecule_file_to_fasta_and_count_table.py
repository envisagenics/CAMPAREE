"""
2019-04-30

This script reads a molecule file generated by CAMPAREE, counts the number of
occurrences of each transcript, and generated a FASTA file of these sequences,
as well as a table of counts for each molecule. Note, this version of the script
is designed to work with a molecule file that just contains mature mRNA sequences
and completely unspliced pre-mRNA (contain all introns). It might still work with
molecule files that contain molecule-specific edits or splicing events, but it
was not designed to work specifically in this scenario.

Note, while a molecule file contains start coordinates and cigar strings mapping
a transcript molecule back to both the custom genome and the original reference
genome, but the transcript headers for each FASTA file only include the information
for the reference.

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
            raise Exception(f"The following output directory does not exist:\n{output_directory}")
        if not os.path.isfile(molecule_file):
            raise Exception(f"The following molecule file does not exist:\n{molecule_file}")

        self.molecule_file = molecule_file
        self.output_directory = output_directory
        self.parental_suffix_list = ['_1', '_2']

    def execute(self, output_prefix="", separate_by_parent=False, trim_polya_tails=False):

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
                transcript_chr = molecule_data[1]
                # custom_genome_start = molecule_data[2]
                # custom_genome_cigar = molecule_data[3]
                ref_genome_start = molecule_data[4]
                ref_genome_cigar = molecule_data[5]
                transcript_strand = molecule_data[6]
                transcript_seq = molecule_data[7]

                if trim_polya_tails:
                    trimmed_seq, trimmed_cigar = self._trim_tail_and_cigar(transcript_seq,
                                                                           ref_genome_cigar,
                                                                           transcript_strand)
                    transcript_seq = trimmed_seq
                    ref_genome_cigar = trimmed_cigar

                if not counts_by_transcript.get(transcript_id, None):
                    counts_by_transcript[transcript_id] = 1
                    sequences_by_transcript[transcript_id] = transcript_seq
                    molecule_metadata = [transcript_chr, ref_genome_start, ref_genome_cigar, transcript_strand]
                    fasta_headers_by_transcript[transcript_id] = f">{transcript_id} {';'.join(molecule_metadata)}"
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
    def _trim_tail_and_cigar(sequence, cigar, strand):
        """
        Helper method which identifies the number (if any) of soft-clipped bases
        at the 3' end of the CIGAR string, trims that many bases from the 3' end
        of the transcript, and removes the soft-clipping entry from the CIGAR string.
        If there is no soft-clipping on the appropriate end of the CIGAR string,
        this method returns the original sequence and CIGAR strings.

        Parameters
        ----------
        sequence : string
            Nucleotide sequence to be trimmed.
        cigar : string
            CIGAR string mapping molecule in the plus-strand orientation.
        strand : string
            Strand molecule is transcribed from. This is used to determine which
            end of the CIGAR string to search for clipped bases.

        Returns
        -------
        tuple
            1 - sequence with tail trimmed from its 5' end (if it had a tail).
            2 - CIGAR string with soft-clipping entry corresponding to tail removed
                (if there was a soft-clipping entry at the appropriate end).

        """
        trimmed_sequence = sequence
        trimmed_cigar = cigar

        # Two regular expression for identifying and extracting the soft-clipping
        # entry from the appropriate and of the CIGAR string, depending upon the
        # transcript's source strand.
        plus_strand_tail_pattern = re.compile('(?P<remaining_cigar>.*?)(?P<soft_clip_pattern>(?P<num_clipped_bases>[0-9]+)S)$')
        minus_strand_tail_pattern = re.compile('^(?P<soft_clip_pattern>(?P<num_clipped_bases>[0-9]+)S)(?P<remaining_cigar>.*?)$')

        if strand == "+" and plus_strand_tail_pattern.match(cigar):
            num_clipped_bases = int(plus_strand_tail_pattern.match(cigar).group("num_clipped_bases"))
            trimmed_cigar = plus_strand_tail_pattern.match(cigar).group("remaining_cigar")
            trimmed_sequence = sequence[:-num_clipped_bases]
        elif strand == "-" and minus_strand_tail_pattern.match(cigar):
            num_clipped_bases = int(minus_strand_tail_pattern.match(cigar).group("num_clipped_bases"))
            trimmed_cigar = minus_strand_tail_pattern.match(cigar).group("remaining_cigar")
            trimmed_sequence = sequence[:-num_clipped_bases]

        return trimmed_sequence, trimmed_cigar

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
        parser.add_argument('-t', '--trim_polya_tails', action='store_true',
                            help="Trim polyA tails from the molecules before returning the"
                                 " FASTA. Tail length determined by soft-clipping at the end"
                                 " of the molecule CIGAR string.")

        args = parser.parse_args()

        molecule_file_converter = MoleculeFileToFastaAndCountTable(molecule_file=args.input_molecule_file,
                                                                   output_directory=args.output_directory)
        molecule_file_converter.execute(output_prefix=args.output_prefix,
                                        separate_by_parent=args.separate_by_parent,
                                        trim_polya_tails=args.trim_polya_tails)

if __name__ == '__main__':
    sys.exit(MoleculeFileToFastaAndCountTable.main())
