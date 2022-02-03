

import law
import luigi
import os

from subprocess import PIPE
from law.util import interruptable_popen

from generation.framework import Task

from RunRivet import RunRivet


class RivetMerge(Task):
    """
    Merge separate YODA files from Rivet analysis runs to a single YODA file 
    """

    # configuration variables
    input_file_name = luigi.Parameter()
    mc_setting = luigi.Parameter()
    chunk_size = luigi.IntParameter()

    exclude_params_req = {
        "chunk_size"
    }


    def convert_env_to_dict(self, env):
        my_env = {}
        for line in env.splitlines():
            if line.find(" ") < 0 :
                try:
                    key, value = line.split("=", 1)
                    my_env[key] = value
                except ValueError:
                    pass
        return my_env


    def set_environment_variables(self):
        code, out, error = interruptable_popen("source {}; env".format(os.path.join(os.path.dirname(__file__),"..","..","..","setup","setup_rivet.sh")),
                                               shell=True, 
                                               stdout=PIPE, 
                                               stderr=PIPE
                                               )
        my_env = self.convert_env_to_dict(out)
        return my_env


    def requires(self):
        return {
            'RunRivet': RunRivet.req(self),
        }


    def remote_path(self, *path):
        parts = (self.__class__.__name__,self.input_file_name, self.mc_setting, ) + path
        return os.path.join(*parts)
    

    def output(self):
        return self.remote_target(
            "{INPUT_FILE_NAME}.yoda".format(
                INPUT_FILE_NAME=str(self.input_file_name)
            )
        )


    def mergeSingleYodaChunk(self, inputfile_list, inputfile_chunk=None):

        print("-------------------------------------------------------")
        print("Starting merging of chunk {}".format(inputfile_chunk))
        print("-------------------------------------------------------")

        # set environment variables
        my_env = self.set_environment_variables()

        # data
        _my_input_file_name = str(self.input_file_name)

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
            print("Input files: {},...,{}".format(inputfile_list[0],inputfile_list[-1]))
            print('Executable: {} {}'.format(" ".join(_rivet_exec + _rivet_args), " ".join([_rivet_in[0],"[...]",_rivet_in[-1]])))
        else:
            print("Input files: {}".format(inputfile_list))
            print('Executable: {}'.format(" ".join(_rivet_exec + _rivet_args + _rivet_in)))
        
        code, out, error = interruptable_popen(
            _rivet_exec + _rivet_args + _rivet_in,
            stdout=PIPE,
            stderr=PIPE,
            env=my_env
        )

        # if successful return merged YODA file
        if(code != 0):
            raise Exception('Error: ' + error + 'Output: ' + out + '\nYodaMerge returned non-zero exit status {}'.format(code))
        else:
            print('Output: ' + out)

        try:
            os.path.exists(output_file)
        except:
            print("Could not find output file {}!".format(output_file))
        
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
            print("Output target doesn't exist!")

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
        while len(final_input_files)>chunk_size:
            final_input_files=self.mergeChunkwise(full_inputfile_list=final_input_files,chunk_size=chunk_size)
        
        _output_file = self.mergeSingleYodaChunk(inputfile_list=final_input_files)

        try:
            os.path.exists(_output_file)
        except:
            print("Could not find output file {}!".format(_output_file))

        output.copy_from_local(_output_file)
        os.system('rm {OUTPUT_FILE}'.format(
            OUTPUT_FILE=_output_file
        ))
        for _outfile in final_input_files:
            os.system('rm {OUTPUT_FILE}'.format(
                OUTPUT_FILE=_outfile
            ))
        

        print("=======================================================")
        
