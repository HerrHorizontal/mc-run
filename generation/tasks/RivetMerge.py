import luigi
from luigi.util import inherits
import os

from generation.framework.utils import run_command, set_environment_variables

from generation.framework.tasks import GenRivetTask, GenerationScenarioConfig

from .RunRivet import RunRivet

from law.logger import get_logger


logger = get_logger(__name__)


@inherits(GenerationScenarioConfig)
class RivetMerge(GenRivetTask):
    """
    Merge separate YODA files from Rivet analysis runs to a single YODA file 
    """

    # configuration variables
    chunk_size = luigi.IntParameter(
        description="Number of individual YODA files to merge in a single `rivet-merge` call."
    )
    mc_generator = luigi.Parameter(
        default="herwig",
        description="Name of the MC generator used for event generation."
    )
    exclude_params_req = {
        "chunk_size",
        "source_script"
    }


    def requires(self):
        return {
            'RunRivet': RunRivet.req(self),
        }


    def remote_path(self, *path):
        parts = (self.__class__.__name__,str(self.mc_generator).lower(),self.campaign, self.mc_setting,) + path
        return os.path.join(*parts)


    def output(self):
        return self.remote_target(
            "{INPUT_FILE_NAME}.yoda".format(
                INPUT_FILE_NAME=str(self.campaign)
            )
        )


    def mergeSingleYodaChunk(self, inputfile_list, inputfile_chunk=None):

        print("-------------------------------------------------------")
        print("Starting merging of chunk {}".format(inputfile_chunk))
        print("-------------------------------------------------------")

        # data
        _my_input_file_name = str(self.campaign)

        # merge the YODA files 
        if inputfile_chunk==None:
            output_file = "{OUTPUT_FILE_NAME}.yoda".format(
                OUTPUT_FILE_NAME=_my_input_file_name
                )
        else:
            output_file = "{OUTPUT_FILE_NAME}_Chunk{BUNCH}.yoda".format(
                OUTPUT_FILE_NAME=_my_input_file_name,
                BUNCH=inputfile_chunk
                )

        _rivet_exec = ["rivet-merge"]
        _rivet_args = [
            "--output={OUTPUT_FILE}".format(OUTPUT_FILE=output_file)
        ]
        _rivet_in = ["-e"] + [
            "{YODA_FILES}".format(YODA_FILES=_yoda_file) for _yoda_file in inputfile_list
        ]

        if len(inputfile_list) > 10:
            logger.info("Input files: {},...,{}".format(inputfile_list[0],inputfile_list[-1]))
            logger.info('Executable: {} {}'.format(" ".join(_rivet_exec + _rivet_args), " ".join([_rivet_in[0],"[...]",_rivet_in[-1]])))
        else:
            logger.info("Input files: {}".format(inputfile_list))
            logger.info('Executable: {}'.format(" ".join(_rivet_exec + _rivet_args + _rivet_in)))

        rivet_env = set_environment_variables(
            os.path.expandvars("$ANALYSIS_PATH/setup/setup_rivet.sh")
        )
        run_command(_rivet_exec+_rivet_args+_rivet_in, env=rivet_env)
        if not os.path.exists(output_file):
            raise IOError("Could not find output file {}!".format(output_file))

        print("-------------------------------------------------------")

        return output_file


    def mergeChunkwise(self, full_inputfile_list, chunk_size): 

        print("-------------------------------------------------------")
        print("Starting splitting of {} files into chunks of {}".format(len(full_inputfile_list),chunk_size))
        print("-------------------------------------------------------")

        inputfile_dict = {
            k: full_inputfile_list[i:i+chunk_size] for k,i in enumerate(range(0,len(full_inputfile_list),chunk_size))
            }
        
        final_input_files = list()
        
        for chunk, inlist in inputfile_dict.iteritems():
            _outfile=self.mergeSingleYodaChunk(inputfile_list=inlist, inputfile_chunk=chunk)
            final_input_files.append(_outfile)
        
        print("-------------------------------------------------------")
        
        return final_input_files


    def run(self):

        # ensure that the output directory exists
        output = self.output()
        try:
            output.parent.touch()
        except IOError:
            logger.error("Output target doesn't exist!")

        # actual payload:
        print("=======================================================")
        print("Starting merging of YODA files")
        print("=======================================================")

        # localize the separate YODA files on grid storage
        inputfile_list = []
        for branch, target in self.input()['RunRivet']["collection"].targets.items():
            if target.exists():
                with target.localize('r') as _file:
                    inputfile_list.append(_file.path)

        # merge in chunks
        chunk_size = self.chunk_size

        final_input_files=inputfile_list
        try:
            while len(final_input_files)>chunk_size:
                final_input_files=self.mergeChunkwise(full_inputfile_list=final_input_files,chunk_size=chunk_size)
            
            _output_file = self.mergeSingleYodaChunk(inputfile_list=final_input_files)
            _output_file = os.path.abspath(_output_file)

            if os.path.exists(_output_file):
                output.copy_from_local(_output_file)
                os.remove(_output_file)
                for _outfile in final_input_files:
                    os.remove(_outfile)
            else:
                raise IOError("Could not find output file {}!".format(_output_file))
        except Exception as e:
            self.output().remove()
            raise e


        print("=======================================================")
