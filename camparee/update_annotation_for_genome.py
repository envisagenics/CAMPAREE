import argparse
import sys
import os
import collections
import bisect
from timeit import default_timer as timer

from beers_utils.sample import Sample
from camparee.camparee_utils import CampareeUtils
from camparee.abstract_camparee_step import AbstractCampareeStep
from camparee.camparee_constants import CAMPAREE_CONSTANTS

class UpdateAnnotationForGenomeStep(AbstractCampareeStep):
    """Updates a gene annotation's coordinates to account for insertions &
    deletions (indels) introduced by GenomeFilesPreparation when it creates
    variant genomes. Note, this is designed to update annotation for a single
    variant genome at a time.

    Parameters
    ----------
    genome_indel_filename : string
        Path to file containing list of indel locations generated by the
        GenomeFilesPreparation. This file has no header and contains three,
        tab-delimited colums (example):
            1:134937	D	2
            1:138813	I	1
        First column = Chromosome and coordinate of indel in the original
                       reference genome. Note, coordinate is zero-based.
        Second column = "D" if variant is a deletion, "I" if variant is an
                        insertion.
        Third column = Length in bases of indel.
    input_annot_filename : string
        Path to file containing gene/transcript annotations using coordinates
        to the original reference genome. This file should have 11, tab-delimited
        columns and includes a header (example):
            chrom  strand  txStart  txEnd exonCount  exonStarts         exonEnds           transcriptID     geneID           geneSymbol  biotype
            1      +       11869    14409 3          11869,12613,13221  12227,12721,14409  ENST00000456328  ENSG00000223972  DDX11L1     pseudogene
        An annotation file with this format can be generated from a GTF file
        using the convert_gtf_to_annot_file_format() function in the Utils
        package. A template for this annotation format is available in the
        class variable Utils.annot_output_format.
    updated_annot_filename : string
        Path to the output file containing gene/transcript annotations with
        coordinates updated to match the variant genome.
    log_filename : string
        Path to the log file.
    """

    #Name of file where script logging is stored
    UPDATE_ANNOT_LOG_FILENAME_PATTERN = CAMPAREE_CONSTANTS.UPDATEANNOT_OUTPUT_FILENAME_PATTERN
    #Name of updated annotation file generated by this script.
    UPDATE_ANNOT_OUTPUT_FILENAME_PATTERN = CAMPAREE_CONSTANTS.UPDATEANNOT_LOG_FILENAME_PATTERN

    def __init__(self, log_directory_path, data_directory_path, parameters=dict()):
        """Short summary.

        Parameters
        ----------
        data_directory_path: string
            Full path to data directory
        log_directory_path : string
            Full path to log directory.
        """
        self.data_directory_path = data_directory_path
        self.log_directory_path = log_directory_path

    def validate(self):
        return True

    def execute(self, sample, genome_indel_suffix, input_annot_file_path, chr_ploidy_file_path):
        """Main work-horse function that generates the updated annotation.

         Parameters
        ----------
        genome_indel_suffix : int
             Suffix to apply to obtain proper genome indel file. Should be 1 or 2.
        input_annot_filename : string
            Full path to annotation file with coordinates for reference genome.
        """

        # Compute which chromosomes we need to have in this annotation
        # If we are in annotation_2, we only want ones with ploidy 2 in this gender
        gender_index = 1 if sample.gender == "female" else 0
        self.chr_ploidy = self._get_chr_ploidy_from_file(chr_ploidy_file_path)
        desired_chromosomes = [chromosome for chromosome, ploidies in self.chr_ploidy.items()
                               if  ploidies[gender_index] >= int(genome_indel_suffix)]

        #TODO: Switch all of these filenames/patterns so they are stored/read
        #      from the CAMPAREE CONSTANTS.
        self.genome_indel_file_path = os.path.join(self.data_directory_path, f"sample{sample.sample_id}",
                                                   f"custom_genome_indels_{genome_indel_suffix}.txt")
        self.input_annot_file_path = input_annot_file_path
        self.updated_annot_file_path = os.path.join(self.data_directory_path, f"sample{sample.sample_id}",
                                                    self.UPDATE_ANNOT_OUTPUT_FILENAME_PATTERN.format(genome_name=genome_indel_suffix))
        self.log_file_path = os.path.join(self.log_directory_path, f'sample{sample.sample_id}',
                                          self.UPDATE_ANNOT_LOG_FILENAME_PATTERN.format(genome_name=genome_indel_suffix))


        #Load indel offsets from the indel file
        indel_offsets = UpdateAnnotationForGenomeStep._get_offsets_from_variant_file(self.genome_indel_file_path)

        with open(self.input_annot_file_path, 'r') as input_annot_file, \
                open(self.updated_annot_file_path, 'w') as updated_annot_file, \
                open(self.log_file_path, 'w') as log_file:

            #Print header for annotation file
            updated_annot_file.write("#" + CampareeUtils.annot_output_format.replace('{', '').replace('}', ''))

            current_chrom = ""

            for annot_feature in input_annot_file:

                annot_feature = annot_feature.rstrip('\n')
                line_data = annot_feature.split('\t')

                if current_chrom != line_data[0]:

                    #Skip header lines (nest in here so it's only checked when
                    #chromosomes change).
                    if annot_feature[0] == '#':
                        continue

                    current_chrom = line_data[0]
                    log_file.write(f"Processing indels and annotated features from chromosome {current_chrom}.\n")

                    if current_chrom in indel_offsets:
                        """
                        Since code below will be performing many lookups and index-
                        based references to the values and keys in current_chrom_variants,
                        it will likely be more efficient to create a list of values
                        and a list of keys from current_chrom_variants once, rather
                        than re-creating them each time the code needs to access a
                        key or value by ordered index.
                        """
                        current_chrom_variant_coords = list(indel_offsets[current_chrom].keys())
                        current_chrom_variant_offsets = list(indel_offsets[current_chrom].values())
                    else:
                        #New chromosome contains no variants
                        log_file.write(f"----No indels from chromosome {current_chrom}.\n")
                        current_chrom_variant_coords = ()
                        current_chrom_variant_coords = ()

                if current_chrom not in desired_chromosomes:
                    continue

                #Current chromosome contains variants
                if current_chrom_variant_coords:

                    tx_start = int(line_data[2])
                    tx_end = int(line_data[3])
                    #exon_count = int(line_data[4])
                    exon_starts = [int(coord) for coord in line_data[5].split(',')]
                    exon_ends = [int(coord) for coord in line_data[6].split(',')]

                    #bisect_right() finds the index at which to insert the given
                    #coordinate in sorted order. Since I'm looking for the
                    #closest coordinate <= the given coordinate, subtract 1 from
                    #the result of bisect_right() to get the correct index.
                    tx_start_offset_index = bisect.bisect_right(current_chrom_variant_coords, tx_start) - 1
                    tx_end_offset_index = bisect.bisect_right(current_chrom_variant_coords, tx_end) - 1

                    #No indels before start of current feature.
                    if tx_start_offset_index == -1:

                        updated_tx_start = tx_start

                        #No indels before end of current feature
                        if tx_end_offset_index == -1:
                            updated_tx_end = tx_end
                            updated_exon_starts = exon_starts
                            updated_exon_ends = exon_ends
                        #First indels occur before end of current feature
                        else:
                            updated_tx_end = tx_end + current_chrom_variant_offsets[tx_end_offset_index]

                            updated_exon_starts = []
                            updated_exon_ends = []
                            for coord in exon_starts:
                                ex_coord_offset_index = bisect.bisect_right(current_chrom_variant_coords, coord) - 1
                                updated_exon_coord = coord
                                if ex_coord_offset_index >= 0:
                                    updated_exon_coord += current_chrom_variant_offsets[ex_coord_offset_index]
                                updated_exon_starts.append(updated_exon_coord)
                            for coord in exon_ends:
                                ex_coord_offset_index = bisect.bisect_right(current_chrom_variant_coords, coord) - 1
                                updated_exon_coord = coord
                                if ex_coord_offset_index >= 0:
                                    updated_exon_coord += current_chrom_variant_offsets[ex_coord_offset_index]
                                updated_exon_ends.append(updated_exon_coord)
                    #No new variants between the start and stop coordinates, so
                    #apply the same offset to all coordinates in the current
                    #feature.
                    elif tx_start_offset_index == tx_end_offset_index:
                        offset = current_chrom_variant_offsets[tx_start_offset_index]
                        updated_tx_start = tx_start + offset
                        updated_tx_end = tx_end + offset
                        updated_exon_starts = [coord+offset for coord in exon_starts]
                        updated_exon_ends = [coord+offset for coord in exon_ends]
                    else:
                        updated_tx_start = tx_start + current_chrom_variant_offsets[tx_start_offset_index]
                        updated_tx_end = tx_end + current_chrom_variant_offsets[tx_end_offset_index]

                        #Update lists of exon starts/ends with correct offsets
                        updated_exon_starts = []
                        updated_exon_ends = []
                        for coord in exon_starts:
                            ex_coord_offset_index = bisect.bisect_right(current_chrom_variant_coords, coord) - 1
                            updated_exon_coord = coord + current_chrom_variant_offsets[ex_coord_offset_index]
                            updated_exon_starts.append(updated_exon_coord)
                        for coord in exon_ends:
                            ex_coord_offset_index = bisect.bisect_right(current_chrom_variant_coords, coord) - 1
                            updated_exon_coord = coord + current_chrom_variant_offsets[ex_coord_offset_index]
                            updated_exon_ends.append(updated_exon_coord)

                    #Format updated annotation data and output
                    updated_annot_file.write(
                        CampareeUtils.annot_output_format.format(
                            chrom=line_data[0],
                            strand=line_data[1],
                            txStart=updated_tx_start,
                            txEnd=updated_tx_end,
                            exonCount=line_data[4],
                            exonStarts=','.join([str(x) for x in updated_exon_starts]),
                            exonEnds=','.join([str(x) for x in updated_exon_ends]),
                            transcriptID=line_data[7],
                            geneID=line_data[8],
                            geneSymbol=line_data[9],
                            biotype=line_data[10]
                        )
                    )

                #No variants in the current chromosome, so no need to update
                #feature coordinates.
                else:
                    updated_annot_file.write(f"{annot_feature}\n")

            #Status message used by is_output_valid() method to determine if
            #this script ran to completion.
            log_file.write("\nALL DONE!")

    def get_commandline_call(self, sample, genome_indel_suffix, input_annot_file_path, chr_ploidy_file_path):
        """
        Prepare command to execute the UpdateAnnotationForGenomeStep from the
        command line, given all of the arugments used to run the execute()
        function.

        Parameters
        ----------
        sample : Sample
            Sample for which to update annotation to parental genomes
        genome_indel_suffix : string
            Suffix to apply to obtain proper genome indel file. This suffix is
            also used in the name of the updated annotation file.
        input_annot_file_path : string
            Full path to annotation file with coordinates for reference genome.
        chr_ploidy_file_path : string
            File that maps chromosome names to their male/female ploidy.

        Returns
        -------
        string
            Command to execute on the command line. It will perform the same
            operations as a call to execute() with the same parameters.

        """
        #Retrieve path to the update_annotation_for_genome.py script.
        update_annotation_path = os.path.realpath(__file__)
        #If the above command returns a string with a "pyc" extension, instead
        #of "py", strip off "c" so it points to this script.
        update_annotation_path = update_annotation_path.rstrip('c')

        command = (f" python {update_annotation_path}"
                   f" --log_directory_path {self.log_directory_path}"
                   f" --data_directory_path {self.data_directory_path}"
                   f" --sample '{repr(sample)}'"
                   f" --genome_indel_suffix {genome_indel_suffix}"
                   f" --input_annot_file_path {input_annot_file_path}"
                   f" --chr_ploidy_file_path {chr_ploidy_file_path}")

        return command

    def get_validation_attributes(self, sample, genome_indel_suffix, input_annot_file_path, chr_ploidy_file_path):
        """
        Prepare attributes required by is_output_valid() function to validate
        output generated the UpdateAnnotationForGenomeStep job corresponding to
        the given sample.

        Parameters
        ----------
        sample : Sample
            Sample for which to update annotation to parental genomes
        genome_indel_suffix : string
            Suffix to apply to obtain proper genome indel file. This suffix is
            also used in the name of the updated annotation file.
        input_annot_file_path : string
            Full path to annotation file with coordinates for reference genome.
        chr_ploidy_file_path : string
            File that maps chromosome names to their male/female ploidy.

        Returns
        -------
        dict
            A UpdateAnnotationForGenomeStep job's data_directory, log_directory,
            sample_id, and the suffix used when building the updated genome
            sequence.

        """
        validation_attributes = {}
        validation_attributes['data_directory'] = self.data_directory_path
        validation_attributes['log_directory'] = self.log_directory_path
        validation_attributes['sample_id'] = sample.sample_id
        validation_attributes['genome_name'] = genome_indel_suffix
        return validation_attributes

    @staticmethod
    def _get_chr_ploidy_from_file(chr_ploidy_filename):
        #TODO: Check to see if this is redundant with CampareeUtils.create_chr_ploidy_data().
        chr_ploidy = dict()
        with open(chr_ploidy_filename) as chr_ploidy_file:
            chr_ploidy_file.readline() # Header line
            for line in chr_ploidy_file:
                chrom, male, female = line.strip().split("\t")
                chr_ploidy[chrom] = (int(male), int(female))
        return chr_ploidy

    @staticmethod
    def _get_offsets_from_variant_file(genome_indel_filename):
        """Read indel file, calculate rolling offset at each variant position
        and return results as a dictionary of ordered dictionaries, indexed by
        chromoeomse name.

        This method requires the genome_indel_filename attribute is set and
        contains a valid filename.

        Parameters
        ----------
        genome_indel_filename : string
            Full path to indel file generated by GenomeFilesPreparation. This
            file must be sorted by chromosome (any sorting order) and by indel
            coordinate (numerical order).

        Returns
        -------
        OrderedDict nested in defaultdict
            Ordered collection of rolling offsets for each chromosome.
            For outer defaultdict:
                Key = chromosome/contig name from indel file
                Value = OrderedDict (see below)
            For inner OrderedDict:
                Key = chromosomal coordinate of variant position
                Value = rolling offest at variant position
            So variant_offsets["chr1"][12345] stores the rolling offset at
            position 12345 on chromosome 1.

        """

        with open(genome_indel_filename, 'r') as genome_indel_file:

            """
            By using the defaultdict object, I can specify the default value
            used every time I create a new key. This way, I don't need to
            include code to check and instantiate keys with empty OrderedDict
            objects. It's all handed by the defaultdict
            """
            variant_offsets = collections.defaultdict(collections.OrderedDict)
            rolling_offset = 0
            curr_chrom = ""

            for line in genome_indel_file:
                line_data = line.split('\t')
                indel_chrom, indel_position = line_data[0].split(':')
                indel_position = int(indel_position)
                indel_type = line_data[1]
                indel_offset = int(line_data[2])

                #Reset rolling offset for new chromosome
                if curr_chrom != indel_chrom:
                    rolling_offset = 0
                    curr_chrom = indel_chrom

                #If variant is a deletion, make offset negative so it subtracts
                #from the rolling offset.
                if indel_type == 'D':
                    indel_offset *= -1

                rolling_offset += indel_offset
                variant_offsets[indel_chrom][indel_position] = rolling_offset

            return variant_offsets

    @staticmethod
    def is_output_valid(validation_attributes):
        """
        Check if output of UpdateAnnotationForGenomeStep for a specific job/
        execution is correctly formed and valid, given a job's data directory,
        log directory, and sample id. Prepare these attributes for a given
        sample's jobs using the get_validation_attributes() method.

        Parameters
        ----------
        validation_attributes : dict
            A job's data_directory, log_directory, sample_id, and the suffix used
            when building the updated genome sequence.

        Returns
        -------
        boolean
            True  - UpdateAnnotationForGenomeStep output files were created and
                    are well formed.
            False - UpdateAnnotationForGenomeStep output files do not exist or
                    are missing data.

        """
        data_directory = validation_attributes['data_directory']
        log_directory = validation_attributes['log_directory']
        sample_id = validation_attributes['sample_id']
        genome_name = validation_attributes['genome_name']

        valid_output = False

        update_annot_outfile_path = os.path.join(data_directory, f"sample{sample_id}",
                                                 UpdateAnnotationForGenomeStep.UPDATE_ANNOT_OUTPUT_FILENAME_PATTERN.format(genome_name=genome_name))
        update_annot_logfile_path = os.path.join(log_directory, f"sample{sample_id}",
                                                 UpdateAnnotationForGenomeStep.UPDATE_ANNOT_LOG_FILENAME_PATTERN.format(genome_name=genome_name))

        if os.path.isfile(update_annot_outfile_path) and \
           os.path.isfile(update_annot_logfile_path):
            #Read last line in update_annotation_for_genome log file
            line = ""
            with open(update_annot_logfile_path, "r") as update_annot_log_file:
                for line in update_annot_log_file:
                    line = line.rstrip()
            if line == "ALL DONE!":
                valid_output = True

        return valid_output

    @staticmethod
    def main():
        """Entry point into script when called directly.

        Parses arguments, gathers input and output filenames, and calls scripts
        that perform the actual operation.

        """
        parser = argparse.ArgumentParser(description='Update annotation file with'
                                                     ' coordinates for variant genome')
        parser.add_argument('-l', '--log_directory_path', required=True,
                            help="Path to log directory.")
        parser.add_argument('-d', '--data_directory_path', required=True,
                            help='Path to data directory')
        parser.add_argument('-g', '--genome_indel_suffix', required=True, type=int, choices=[1,2],
                            help="Integer suffix that distinguishes genome names")
        parser.add_argument('-i', '--input_annot_file_path', required=True,
                            help="Annotation file using reference coordinates")
        parser.add_argument('-p', '--chr_ploidy_file_path')
        parser.add_argument('--sample', default=None,
                            help='String representation of a Sample object. Must provide '
                                 'this argument or the "--sample_id".')
        parser.add_argument('-s', '--sample_id', type=int, default=None,
                            help='sample name in vcf when prepended with sample. Overrides'
                                 ' id from the "--sample" argument, if it is provided.')

        args = parser.parse_args()

        update_annotation = UpdateAnnotationForGenomeStep(args.log_directory_path,
                                                          args.data_directory_path)
        if args.sample:
            sample = eval(args.sample)
        else:
            #Create dummy sample for debug purposes.
            sample = Sample(None, "debug sample", None, None, None)

        #Update sample with sample_id, if specified.
        if args.sample_id:
            sample.sample_id = args.sample_id

        update_annotation.execute(sample=sample,
                                  genome_indel_suffix=args.genome_indel_suffix,
                                  input_annot_file_path=args.input_annot_file_path,
                                  chr_ploidy_file_path=args.chr_ploidy_file_path)

if __name__ == '__main__':
    sys.exit(UpdateAnnotationForGenomeStep.main())

'''
python update_annotation_for_genome.py \
-i '../../resources/index_files/GRCh38/Homo_sapiens.GRCh38.92.annotation.sorted_to_match_fasta.txt' \
-s 1 \
-g 1 \
-d ../../data/pipeline_results_run99/expression_pipeline/data \
-l ../../data/pipeline_results_run99/expression_pipeline/logs
'''
