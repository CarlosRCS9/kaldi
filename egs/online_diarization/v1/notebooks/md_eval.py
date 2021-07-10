import subprocess
import re

def md_eval(ref_filepath, res_filepath, save_filepath = None):
    bin = '../../../../tools/sctk-2.4.10/src/md-eval/md-eval.pl'
    p = subprocess.Popen([bin, '-r', ref_filepath, '-s', res_filepath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    rc = p.returncode
    if rc == 0:
        output = output.decode("utf-8")
        if save_filepath is not None:
            file = open(save_filepath, 'w')
            file.write(output)
            file.close()
        lines =  output.split('\n')
        derLine = [line for line in lines if 'OVERALL SPEAKER DIARIZATION ERROR' in line][0]
        return float(re.findall('\d+\.\d+', derLine)[0])
    else:
        exit('md-eval.pl fail')