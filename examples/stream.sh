pip uninstall opencv-python
pip uninstall opencv-python-headless
sudo apt install libgtk2.0-dev pkg-config cmake
pip install opencv-python
export CAMERA_URI="rtsp://${CAMERA_IP}/live.sdp"
python innofw/onvif_util/stream.py --uri $CAMERA_URI