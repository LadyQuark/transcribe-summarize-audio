Create an environment and install all packages

```
conda create --name transcribe python=3.8.13

conda activate transcribe

conda install notebook nb_conda_kernels

pip3 install -r requirements.txt
```
   

Create `.env` from `.env.example`


`whisper` also requires the command-line tool [`ffmpeg`](https://ffmpeg.org/) to be installed on your system, which is available from most package managers:

```bash
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```