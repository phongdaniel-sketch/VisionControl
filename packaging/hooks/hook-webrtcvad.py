from PyInstaller.utils.hooks import copy_metadata

# The project uses the maintained wheels distribution, not legacy webrtcvad.
datas = copy_metadata('webrtcvad-wheels')
hiddenimports = ['_webrtcvad']
