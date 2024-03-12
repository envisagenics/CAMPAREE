from collections import namedtuple
import os

CampareeConstants = namedtuple('Constants',
                               ['CAMPAREE_ROOT_DIR',
                                'CAMPAREE_OUTPUT_DIR_NAME',
                                'DEFAULT_STAR_OUTPUT_PREFIX',
                                'DEFAULT_STAR_BAM_FILENAME',
                                'INTRON_OUTPUT_FILENAME',
                                'INTRON_OUTPUT_ANTISENSE_FILENAME',
                                'INTERGENIC_OUTPUT_FILENAME',
                                'VARIANTS_FINDER_OUTPUT_FILENAME',
                                'VARIANTS_FINDER_LOG_FILENAME',
                                'VARIANTS_COMPILATION_OUTPUT_FILENAME',
                                'VARIANTS_COMPILATION_LOG_FILENAME',
                                'BEAGLE_OUTPUT_PREFIX',
                                'BEAGLE_OUTPUT_FILENAME',
                                'BEAGLE_LOG_FILENAME',
                                'GENOMEBUILDER_SEQUENCE_FILENAME_PATTERN',
                                'GENOMEBUILDER_INDEL_FILENAME_PATTERN',
                                'GENOMEBUILDER_LOG_FILENAME',
                                'UPDATEANNOT_OUTPUT_FILENAME_PATTERN',
                                'UPDATEANNOT_LOG_FILENAME_PATTERN',
                                'TRANSCRIPTOME_FASTA_OUTPUT_FILENAME_PATTERN',
                                'TRANSCRIPTOME_FASTA_LOG_FILENAME_PATTERN',
                                'KALLISTO_INDEX_DIR_PATTERN',
                                'KALLISTO_INDEX_FILENAME_PATTERN',
                                'KALLISTO_INDEX_LOG_FILENAME_PATTERN',
                                'KALLISTO_QUANT_DIR_PATTERN',
                                'KALLISTO_ABUNDANCE_FILENAME',
                                'KALLISTO_QUANT_LOG_FILENAME_PATTERN',
                                'TXQUANT_OUTPUT_TX_FILENAME',
                                'TXQUANT_OUTPUT_GENE_FILENAME',
                                'TXQUANT_OUTPUT_PSI_FILENAME',
                                'TXQUANT_LOG_FILENAME',
                                'BOWTIE2_INDEX_DIR_PATTERN',
                                'BOWTIE2_INDEX_PREFIX_PATTERN',
                                'BOWTIE2_INDEX_LOG_FILENAME_PATTERN',
                                'BOWTIE2_ALIGN_FILENAME_PATTERN',
                                'BOWTIE2_ALIGN_LOG_FILENAME_PATTERN',
                                'ALLELIC_IMBALANCE_OUTPUT_FILENAME',
                                'ALLELIC_IMBALANCE_LOG_FILENAME',
                                'MOLECULE_MAKER_OUTPUT_OPTIONS_W_EXTENSIONS',
                                'MOLECULE_MAKER_OUTPUT_FILENAME_PATTERN',
                                'MOLECULE_MAKER_DEFAULT_NUM_MOLECULES_PER_PACKET',
                                'MOLECULE_MAKER_LOG_FILENAME'])

CampareeConstants.__doc__ = """
Provides a list of constants specific to the CAMPAREE pipeline.
These include input/output/logging filenames used by various
steps in the pipeline.
"""

_CAMPAREE_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The following variables are used to add prefixes to string patterns defined
# in the namedtuple below.
_DEFAULT_STAR_OUTPUT_PREFIX="genome_alignment."
# Prefix for names of all (non-log) files generated by GenomeBuilderStep
_DEFAULT_GENOMEBUILDER_OUTPUT_PREFIX="custom_genome"
CAMPAREE_CONSTANTS = \
    CampareeConstants(CAMPAREE_ROOT_DIR=_CAMPAREE_ROOT_DIR,
                      # Name of sub-directory containing CAMPAREE results in output directory.
                      CAMPAREE_OUTPUT_DIR_NAME="CAMPAREE",
                      # Prefix this pipeline assigns to the STAR output files (excluding path),
                      # if the user does not provide pre-aligned BAM files. This is part of what
                      # is passed STAR as a command line parameter.
                      DEFAULT_STAR_OUTPUT_PREFIX=_DEFAULT_STAR_OUTPUT_PREFIX,
                      # Full name (exlcuding path) of STAR-created BAM file generated by this
                      # pipeline. The same filename is used across all samples.
                      DEFAULT_STAR_BAM_FILENAME=_DEFAULT_STAR_OUTPUT_PREFIX + "Aligned.sortedByCoord.out.bam",
                      INTRON_OUTPUT_FILENAME="intron_quantifications.txt",
                      INTRON_OUTPUT_ANTISENSE_FILENAME="intron_antisense_quantifications.txt",
                      INTERGENIC_OUTPUT_FILENAME="intergenic_quantifications.txt",
                      # Name of file where VariantsFinderStep output is stored.
                      VARIANTS_FINDER_OUTPUT_FILENAME="variants.txt",
                      # Name of file where VariantsFinderStep logging is stored.
                      VARIANTS_FINDER_LOG_FILENAME="VariantsFinderStep.log",
                      # Name of file where VariantsCompilationStep output is stored.
                      VARIANTS_COMPILATION_OUTPUT_FILENAME="all_variants.vcf",
                      # Name of file where VariantsCompilationStep logging is stored.
                      VARIANTS_COMPILATION_LOG_FILENAME="VariantsCompilationStep.log",
                      # Prefix assigned to all beagle output files. This is part of what is passed
                      # to beagle as a command line parameter.
                      BEAGLE_OUTPUT_PREFIX="beagle",
                      # Name of output file generated by the beagle program.
                      BEAGLE_OUTPUT_FILENAME="beagle.vcf.gz",
                      # Name of file where BeagleStep logging is stored.
                      BEAGLE_LOG_FILENAME="BeagleStep.log",
                      # String pattern to construct sequence FASTA filename generated by GenomeBuilderStep
                      GENOMEBUILDER_SEQUENCE_FILENAME_PATTERN=_DEFAULT_GENOMEBUILDER_OUTPUT_PREFIX + '_{genome_name}.fa',
                      # String pattern to construct indel filename generated by GenomeBuilderStep
                      GENOMEBUILDER_INDEL_FILENAME_PATTERN=_DEFAULT_GENOMEBUILDER_OUTPUT_PREFIX + '_indels_{genome_name}.txt',
                      # Name of file where GenomeBuilderStep logging is stored
                      GENOMEBUILDER_LOG_FILENAME="GenomeBuilderStep.log",
                      # Name of updated annotation file generated by UpdateAnnotationForGenomeStep
                      UPDATEANNOT_OUTPUT_FILENAME_PATTERN='updated_annotation_{genome_name}.txt',
                      # Name of file where UpdateAnnotationForGenomeStep logging is stored
                      UPDATEANNOT_LOG_FILENAME_PATTERN='UpdateAnnotationForGenomeStep_{genome_name}.log',
                      # Name of transcriptome FASTA file generated by TranscriptomeFastaPreparationStep
                      TRANSCRIPTOME_FASTA_OUTPUT_FILENAME_PATTERN='transcriptome_{genome_name}.fa',
                      # Name of file where TranscriptomeFastaPreparationStep logging is stored
                      TRANSCRIPTOME_FASTA_LOG_FILENAME_PATTERN='TranscriptomeFastaPreparationStep_{genome_name}.log',
                      # Name of directory to store kallisto index files
                      KALLISTO_INDEX_DIR_PATTERN='transcriptome_{genome_name}_kallisto_index',
                      # String pattern to construct path to kallisto index file
                      KALLISTO_INDEX_FILENAME_PATTERN='transcriptome_{genome_name}.kallisto.index',
                      # Name of file where KallistoIndexStep logging is stored
                      KALLISTO_INDEX_LOG_FILENAME_PATTERN='KallistoIndexStep_{genome_name}.log',
                      # Name of directory to store kallisto quantification results
                      KALLISTO_QUANT_DIR_PATTERN='transcriptome_{genome_name}_kallisto_quant',
                      # Name of transcript quantification output file created by kallisto.
                      KALLISTO_ABUNDANCE_FILENAME='abundance.tsv',
                      # Name of file where KallistoQuantStep logging is stored
                      KALLISTO_QUANT_LOG_FILENAME_PATTERN='KallistoQuantStep_{genome_name}.log',
                      # Name of transcript-level counts file generated by TranscriptGeneQuantificationStep
                      TXQUANT_OUTPUT_TX_FILENAME="transcript_quantifications.txt",
                      # Name of gene-level counts file generated by TranscriptGeneQuantificationStep
                      TXQUANT_OUTPUT_GENE_FILENAME="gene_quantifications.txt",
                      # Name of PSI values file generated by TranscriptGeneQuantificationStep
                      TXQUANT_OUTPUT_PSI_FILENAME="isoform_psi_value_quantifications.txt",
                      # Name of file where TranscriptGeneQuantificationStep logging is stored
                      TXQUANT_LOG_FILENAME="TranscriptGeneQuantificationStep.log",
                      # Name of directory to store Bowtie2 index files.
                      BOWTIE2_INDEX_DIR_PATTERN='transcriptome_{genome_name}_bowtie2_index',
                      # Prefix used by Bowtie2 when naming/creating all index files
                      BOWTIE2_INDEX_PREFIX_PATTERN='bowtie2_transcriptome_{genome_name}',
                      # Name of file where Bowtie2IndexStep logging is stored
                      BOWTIE2_INDEX_LOG_FILENAME_PATTERN='Bowtie2IndexStep_{genome_name}.log',
                      # Name of file where Bowtie2 alignment results are stored
                      BOWTIE2_ALIGN_FILENAME_PATTERN='Bowtie2_transcriptome_alignment_{genome_name}.sam',
                      # Name of file where Bowtie2AlignStep logging is stored
                      BOWTIE2_ALIGN_LOG_FILENAME_PATTERN='Bowtie2AlignStep_{genome_name}.log',
                      # Name of file where allelic imbalance distribution stored
                      ALLELIC_IMBALANCE_OUTPUT_FILENAME="allelic_imbalance_quantifications.txt",
                      # Name of file where AllelicImbalanceQuantificationStep logging is stored
                      ALLELIC_IMBALANCE_LOG_FILENAME="AllelicImbalanceQuantificationStep.log",
                      # Dictionary mapping the options for molecule output type, to the
                      # extension of the output file. Note: the keys are used to validate
                      # the output type entered in the config file.
                      MOLECULE_MAKER_OUTPUT_OPTIONS_W_EXTENSIONS={"file": "txt", "packet": "pickle", "generator": ''},
                      # Name of files where molecule representations are stored.
                      MOLECULE_MAKER_OUTPUT_FILENAME_PATTERN='molecule_{output_type}{packet_num}.{extension}',
                      # Default number of molecules to store per molecule packet, if the
                      # output type is set to packet.
                      MOLECULE_MAKER_DEFAULT_NUM_MOLECULES_PER_PACKET=10_000,
                      # Name of file where MoleculeMakerStep logging is stored
                      MOLECULE_MAKER_LOG_FILENAME="MoleculeMakerStep.log"
                      )

CAMPAREE_VERSION="0.4.1"
