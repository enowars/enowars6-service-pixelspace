import os
import sys
import subprocess


def print_help():
    print("Options:\n --prune-all | -pa\t\truns docker system prune -a -f --volumes")


def run_bash_command_as_subprocess(command: str):
    print(command)
    process = subprocess.Popen(command.split(),stdout=subprocess.PIPE)
    output,error = process.communicate()
    if error == None:
        print("SUCCESS")
    else:
        print(f"ERROR: {error}")
    print(f"\n{output.decode('utf-8')}")
    print("PROCESS FINISHED")



if __name__ == "__main__":
    if sys.argv[1] in ['--help', '-h']:
        print_help()

    if sys.argv[1] in ['--prune-all', '-pa']:
        run_bash_command_as_subprocess("docker system prune -a -f --volumes")
    
    if sys.argv[1] in ['--build','-b']:
        dir = ""
        flags = "None"
        if len(sys.argv) == 3:
            dir = sys.argv[2]
            
        elif len(sys.argv) == 4:
            flags = sys.argv[2]
            dir = sys.argv[3]
        print(f"Building containers with flags: {flags}")
        
        os.chdir(os.path.join(os.getcwd(),dir))
        print(f"Current directory: {os.getcwd()}")
        if flags == "None":
            run_bash_command_as_subprocess(f"docker-compose build")
        else:
            run_bash_command_as_subprocess(f"docker-compose build {flags}")
    
    if sys.argv[1] in ['--up','-u']:
        dir = ""
        flags = "None"
        if len(sys.argv) == 3:
            dir = sys.argv[2]
        elif len(sys.argv) == 4:
            flags = sys.argv[2]
            dir = sys.argv[3]
        os.chdir(os.path.join(os.getcwd(),dir))
        print(f"Current directory: {os.getcwd()}")
        if flags == "None":
            run_bash_command_as_subprocess(f"docker-compose up")
        else:
            run_bash_command_as_subprocess(f"docker-compose up {flags}")
    
    if sys.argv[1] in ['--build-up','-bu']:
        dir = ""
        flags = "None"
        if len(sys.argv) == 3:
            dir = sys.argv[2]
        print(f"Building AND starting containers")
        os.chdir(os.path.join(os.getcwd(),dir))
        run_bash_command_as_subprocess("docker-compose build")
        run_bash_command_as_subprocess("docker-compose up")