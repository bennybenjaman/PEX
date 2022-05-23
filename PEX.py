#!/usr/bin/env python3

# sz0 >#$

#  >======>   >=======> >=>      >=>
#  >=>    >=> >=>        >=>   >=>
#  >=>    >=> >=>         >=> >=>
#  >  ======>   >=====>       >=>
#  >=>        >=>         >=> >=>
#  >=>        >=>        >=>   >=>
#  >=>        >=======> >=>      >=>

# PYTHON FRONTEND FOR BRAZEN RTSP CAMERA FIRMWARE
# OFFLOADS RECORDINGS FROM CAMERA/MIC TO REMOTE CLIENT APPLICATION
# ONLY INTENDED FOR BRAZEN RASPI AND ODROID C2/XU4 HOSTAPD FIRMWARE VARIANTS
# PLACE SSH KEY GENERATED BY BRAZEN FIRMWARE SETUP INTO THE SSH FOLDER
# INSTALL REQUIREMENTS.TXT,PYTHON3, AND TMUX BEFORE RUNNING.
# RECORDINGS ARE SAVED IN $HOME/Videos/yeardatehourmin.mp4
# pip3 install -r requirements.txt
# sudo apt install python3 tmux
# TO RUN PEX: python3 PEX.py


import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk
import sv_ttk
import time
import tkinter.messagebox
import subprocess
import sys
import signal
import psutil
import os
from os import getpid
from io import StringIO

# root.configure()
root = tk.Tk()
root.geometry("1080x720")
root.resizable(False, False)
sv_ttk.use_dark_theme()
var = StringVar(root, 1)


# Background
canvas = Canvas(width=1080, height=720)
canvas.grid(row=0, column=0, rowspan=6, columnspan=4)
image = tk.PhotoImage(file="./Images/background_images/background.png")
canvas.create_image(0, 0, image=image, anchor=NW)

# FRAMES
system_frame_left = tk.Frame(root, width=800, height=545)
system_frame_left.grid(row=0, column=0, pady=0, sticky="NW")
system_frame_right = tk.Frame(root, width=800, height=540)
system_frame_right.grid(row=0, column=3, pady=(10, 0), padx=(0, 10), sticky="NW")
system_frame_bottom = tk.Frame(root, width=850, height=100)
system_frame_bottom.grid(row=1, column=0, pady=(20, 0), padx=(15, 0), sticky="NW")
VIDEO_FRAME = tk.Frame(system_frame_left, width=850, height=525)
VIDEO_FRAME_ID = VIDEO_FRAME.winfo_id()
rxvt_frame = tk.Frame(system_frame_left, width=850, height=545)
rxvt_frame_id = system_frame_left.winfo_id()
#PEX_LOG_FRAME = tk.Frame(root, width=800, height=545)
#PEX_LOG_FRAME.grid(row=0, column=0, pady=0, sticky="NW")
#pex_log_frame = tk.Text(system_frame_left, width=800, height=545)
#pex_log_frame.grid(row=0, column=0, pady=0, sticky="NW")

# VARIABLES
TMUX_REMOTE_DETACH = "tmux detach -s Pex-remote-Term"
TMUX_REMOTE_ATTACH = "tmux attach -s Pex-remote-Term"
TMUX_LOCAL_DETACH = "tmux detach -s Pex-remote-Term"
TMUX_LOCAL_ATTACH = "tmux attach -t Pex-Local-Term"
TMUX_REMOTE_CREATE = "tmux new -s Pex-remote-Term -d"
TMUX_LOCAL_CREATE = "tmux new -s Pex-Local-Term -d"
TMUX_SSH_LOGIN = ""'tmux send -t Pex-remote-Term "ssh -p22 -i ./ssh/rtsp-cam-1 root@192.168.250.1" ENTER '""

# REMOTE VARIABLES
ssh_camera = "ssh -p22 -i ./ssh/rtsp-cam-1 root@192.168.250.1"
reboot = " shutdown now -r"
shutdown = " poweroff"


# URXVT TERMINALS
URXVT_LOCAL = './bin/urxvt -embed %d -fn xft:dejavusansmono:size=11 -cd "$HOME" -bg black -fg white -e tmux attach -t Pex-Local-Term'
URXVT_REMOTE = './bin/urxvt -embed %d -fn xft:dejavusansmono:size=11 -cd "$HOME" -bg black -fg white -e tmux attach -t Pex-remote-Term'
HI_Q_MPV = './bin/mpv -no-cache --untimed -hdr-compute-peak=no --no-demuxer-thread --vd-lavc-threads=1 --wid=%d --vf=removegrain,colortemperature:8000,curves:darker rtsp://192.168.250.1:8554/camera'
TWOX_ZOOM_MPV = './bin/mpv -no-cache -hdr-compute-peak=no --untimed --no-demuxer-thread --video-sync=audio --vd-lavc-threads=1 --wid=%d rtsp://192.168.250.1:8554/zoom'
VIDEO_WITH_AUDIO_MPV = './bin/mpv -no-cache --untimed -hdr-compute-peak=no --no-demuxer-thread --video-sync=audio --vd-lavc-threads=1 --wid=%d rtsp://192.168.250.1:8554/camera-audio'
AUDIO_ONLY_MPV = './bin/mpv -no-cache --untimed -hdr-compute-peak=no --no-demuxer-thread --video-sync=audio --vd-lavc-threads=1 --wid=%d rtsp://192.168.250.1:8554/audio'
NIGHTVISION_MPV = './bin/mpv -no-cache --untimed -hdr-compute-peak=no --no-demuxer-thread --video-sync=audio --vd-lavc-threads=1 --vf=unsharp=luma_msize_x=9:luma_msize_y=9:luma_amount=3 --vf=eq=gamma=1.8 --wid=%d rtsp://192.168.250.1:8554/nightvision'
HI_Q_RECORDING_PROCESS = "./bin/ffmpeg -i rtsp://@192.168.250.1:8554/camera -acodec copy -vcodec copy $HOME/Videos/$(date +""%Y-%m-%d-%T"").mp4"
TWOX_RECORDING_PROCESS = "./bin/ffmpeg -i rtsp://@192.168.250.1:8554/zoom -acodec copy -vcodec copy $HOME/Videos/$(date +""%Y-%m-%d-%T"").mp4"
LOW_Q_AUDIO_RECORDING_PROCESS = "./bin/ffmpeg -i rtsp://@192.168.250.1:8554/camera-audio -acodec copy -vcodec copy $HOME/Videos/$(date +""%Y-%m-%d-%T"").mp4"
AUDIO_ONLY_RECORDING_PROCESS = "./bin/ffmpeg -i rtsp://@192.168.250.1:8554/camera-audio-only -acodec copy -vcodec copy $HOME/Videos/$(date +""%Y-%m-%d-%T"").mp4"
NIGHTVISION_RECORDING_PROCESS = "./bin/ffmpeg -i rtsp://@192.168.250.1:8554/nightvision -acodec copy -vcodec copy $HOME/Videos/$(date +""%Y-%m-%d-%T"").mp4"

# FUNCTIONS
# ---------


# TMUX STARTUP

def tmux_create_Pex_local():
    subprocess.call(TMUX_LOCAL_CREATE, shell=True)
    pass


def tmux_create_Pex_remote():
    subprocess.call(TMUX_REMOTE_CREATE, shell=True)


def tmux_create_Pex_remote_ssh_login():
    subprocess.Popen(TMUX_SSH_LOGIN, shell=True)
    pass


# STARTUP RXVT SUBPROCESS
def rxvt():
    tmux_create_Pex_local()
    tmux_create_Pex_remote()
    tmux_create_Pex_remote_ssh_login()
    rxvt_frame = tk.Frame(system_frame_left, width=850, height=548, bg="#000000")
    rxvt_frame.grid(row=0, column=0, pady=(0, 0), padx=(0, 0), sticky="NW")
    rxvt_frame_id = system_frame_left.winfo_id()
    urxv_remote = subprocess.Popen('urxvt -embed %d -fn xft:dejavusansmono:size=11 -cd "" -bg black -fg white -e tmux attach -t Pex-remote-Term' % rxvt_frame_id, shell=True)


# ATTACHED TO RADIO BUTTON REMOTE SHELL
def tmux_remote_term_swap():
    subprocess.Popen('tmux -t Pex-Local-Term -d', shell=True)
    subprocess.call('killall urxvt', shell=True)
    subprocess.Popen(URXVT_REMOTE % rxvt_frame_id, shell=True)
    raise_console()


# ATTACHED TO RADIO BUTTON LOCAL SHELL
def tmux_local_term_swap():
    subprocess.Popen('tmux -t Pex-remote-Term -d; ENTER', shell=True)
    subprocess.call('killall urxvt', shell=True)
    subprocess.Popen(URXVT_LOCAL % rxvt_frame_id, shell=True)
    raise_console()


# ATTACHED TO FFMPEG LOG BUTTON
def FFMPEG_LOG():
    raise_console()
    FFMPEG = subprocess.Popen('tmux send -t Pex-Local-Term "ssh -p22 -i ./ssh/rtsp-cam-1 root@192.168.250.1" ENTER && tmux send -t Pex-Local-Term "tail -f /var/log/ff" ENTER ', shell=True)


# ATTACHED TO RTSP LOG BUTTON
def RTSP_LOG():
    raise_console()
    RTSP = subprocess.Popen('tmux send -t Pex-Local-Term "ssh -p22 -i ./ssh/rtsp-cam-1 root@192.168.250.1" ENTER && tmux send -t Pex-Local-Term "tail -f /var/log/ff.log" ENTER', shell=True)


# ATTACHED TO WIFI CONNECTIONS BUTTON
def wifi_connect():
    raise_console()
    WIFI = subprocess.Popen('tmux send -t Pex-Local-Term "nmtui" ENTER', shell=True)


# ATTACHED TO TEST SIGNAL BUTTON
def test_signal():
    raise_console()
    SIGNAL = subprocess.Popen('tmux send -t Pex-Local-Term "wavemon" ENTER', shell=True)


# ATTACHED TO HTOP BUTTON
def HTOP():
    raise_console()
    HTOP = subprocess.Popen('tmux send -t Pex-Local-Term "ssh -p22 -i ./ssh/rtsp-cam-1 root@192.168.250.1" ENTER && tmux send -t Pex-Local-Term "htop" ENTER', shell=True)


# ATTACHED TO CONSOLE BUTTON
def show_console():
    raise_console()


# ATTACHED TO KILL STREAM BUTTON
def kill_stream():
    KILL_RTSP = subprocess.Popen(ssh_camera + " systemctl start kill-rtsp.service", shell=True)


# ATTACHED TO SHUTDOWN BUTTON
def reb_shut_choice(option):
    pop.destroy()
    if option == "REBOOT":
        subprocess.Popen(ssh_camera + reboot, shell=True)
    else:
        subprocess.Popen(ssh_camera + shutdown, shell=True)


# ATTACHED TO HI-Q-VIDEO BUTTON
def Hi_Q():
    global HI_Q
    global HI_Q_process
    subprocess.Popen(ssh_camera + " /usr/local/bin/camera && exit", shell=True)
    VIDEO_FRAME = tk.Frame(root, width=850, height=525,)
    VIDEO_FRAME.grid(row=0, column=0, pady=(0, 0), padx=(0, 0), sticky="NW")
    VIDEO_FRAME_ID = VIDEO_FRAME.winfo_id()
    time.sleep(5)
    HI_Q_process = subprocess.Popen("exec " + HI_Q_MPV % VIDEO_FRAME_ID, shell=True)
    # CONSOLE BACKGROUND IMAGE
    console_background_img = ImageTk.PhotoImage(Image.open("./Images/background_images/CONSOLE_BACKGROUND_IMAGE.png"))
    console_background = Label(VIDEO_FRAME, image=console_background_img, bd=0)
    console_background.place(x=0, y=0)
    console_background.image = console_background_img


# ATTACHED TO 2X ZOOM BUTTON
def TWOX_ZOOM():
    global TWOX_ZOOM_process
    subprocess.Popen(ssh_camera + " /usr/local/bin/zoom", shell=True)
    VIDEO_FRAME = tk.Frame(root, width=850, height=525,)
    VIDEO_FRAME.grid(row=0, column=0, pady=(0, 0), padx=(0, 0), sticky="NW")
    VIDEO_FRAME_ID = VIDEO_FRAME.winfo_id()
    time.sleep(5)
    TWOX_ZOOM_process = subprocess.Popen("exec " + TWOX_ZOOM_MPV % VIDEO_FRAME_ID, shell=True)
    # CONSOLE BACKGROUND IMAGE
    console_background_img = ImageTk.PhotoImage(Image.open("./Images/background_images/CONSOLE_BACKGROUND_IMAGE.png"))
    console_background = Label(VIDEO_FRAME, image=console_background_img, bd=0)
    console_background.place(x=0, y=0)
    console_background.image = console_background_img


# ATTACHED TO LOW QUALITY VIDEO + AUDIO BUTTON
def VIDEO_WITH_AUDIO():
    global VIDEO_WITH_AUDIO_process
    subprocess.Popen(ssh_camera + " /usr/local/bin/camera-audio", shell=True)
    VIDEO_FRAME = tk.Frame(root, width=855, height=525,)
    VIDEO_FRAME.grid(row=0, column=0, pady=(0, 0), padx=(0, 0), sticky="NW")
    VIDEO_FRAME_ID = VIDEO_FRAME.winfo_id()
    time.sleep(5)
    VIDEO_WITH_AUDIO_process = subprocess.Popen("exec " + VIDEO_WITH_AUDIO_MPV %
    VIDEO_FRAME_ID, shell=True)
    # CONSOLE BACKGROUND IMAGE
    console_background_img = ImageTk.PhotoImage(Image.open("./Images/background_images/CONSOLE_BACKGROUND_IMAGE.png"))
    console_background = Label(VIDEO_FRAME, image=console_background_img, bd=0)
    console_background.place(x=0, y=0)
    console_background.image = console_background_img


# ATTACHED TO AUDIO ONLY BUTTON
def AUDIO_ONLY():
    global AUDIO_ONLY_process
    subprocess.Popen(ssh_camera + " /usr/local/bin/camera-audio-only", shell=True)
    VIDEO_FRAME = tk.Frame(root, width=850, height=525,)
    VIDEO_FRAME.grid(row=0, column=0, pady=(0, 0), padx=(0, 0), sticky="NW")
    VIDEO_FRAME_ID = VIDEO_FRAME.winfo_id()
    time.sleep(5)
    rxvt_frame.grid_forget()
    AUDIO_ONLY_process = subprocess.Popen("exec " + AUDIO_ONLY_MPV % VIDEO_FRAME_ID, shell=True)
    # ADDING "exec " to subprocess is essential for this to work.
    # CONSOLE BACKGROUND IMAGE
    console_background_img = ImageTk.PhotoImage(Image.open("./Images/background_images/CONSOLE_BACKGROUND_IMAGE.png"))
    console_background = Label(VIDEO_FRAME, image=console_background_img, bd=0)
    console_background.place(x=0, y=0)
    console_background.image = console_background_img


def NIGHTVISION():
    subprocess.Popen(ssh_camera + " /usr/local/bin/nightvision", shell=True)
    VIDEO_FRAME = tk.Frame(root, width=850, height=525,)
    VIDEO_FRAME.grid(row=0, column=0, pady=(0, 0), padx=(0, 0), sticky="NW")
    VIDEO_FRAME_ID = VIDEO_FRAME.winfo_id()
    time.sleep(5)
    rxvt_frame.grid_forget()
    AUDIO_ONLY_process = subprocess.Popen("exec " + NIGHTVISION_MPV % VIDEO_FRAME_ID, shell=True)
    # ADDING "exec " to subprocess is essential for this to work.
    # CONSOLE BACKGROUND IMAGE
    console_background_img = ImageTk.PhotoImage(Image.open("./Images/background_images/CONSOLE_BACKGROUND_IMAGE.png"))
    console_background = Label(VIDEO_FRAME, image=console_background_img, bd=0)
    console_background.place(x=0, y=0)
    console_background.image = console_background_img


# FOR PEX_LOG RADIO BUTTON. FIX FRAME PLACEMENT AND STDOUT LINE ORDER/MOT INCLUDED
def pex_log():
    old_stdout = sys.stdout
    sys.stdout = pexstdout = StringIO()
    pex_ouput = Label(PEX_LOG_FRAME, height=12, width=40, text="", bg="grey",borderwidth=5, relief=RIDGE)


# ATTACHED TO RECORD BUTTON. CHEAP. CREATE A BETTER LOOP IN THE FUTURE
def start_recording():
    try:
        subprocess.run(HI_Q_RECORDING_PROCESS, shell=True, timeout=2)
    except TimeoutExpired:
        pass
    try:
        subprocess.run(TWOX_RECORDING_PROCESS, shell=True, timeout=2)
    except TimeoutExpired:
        pass
    try:
        subprocess.run(LOW_Q_AUDIO_RECORDING_PROCESS, shell=True, timeout=2)
    except TimeoutExpired:
        pass
    try:
        subprocess.run(AUDIO_ONLY_RECORDING_PROCESS, shell=True, timeout=2)
    except TimeoutExpired:
        pass
    try:
        subprocess.run(NIGHTVISION_RECORDING_PROCESS, shell=True, timeout=2)
    except TimeoutExpired:
        pass


# FOR FUTURE PROCESS CLEANUP
def get_pid():
    global ffmpeg_pid
    ffmpeg_pid = int(check_output(["pidof", "-s", "ffmpeg"]))
    print("FFMPEG pid: ", ffmpeg_pid)


# FOR FUTURE PROCESS CLEANUP
def kill_pid(pid):
    pass


# ATTACHED TO STOP BUTTON. SENDS SIG-INT TO CLEANLY CLOSE FFMPEG
def stop_recording():
    pid = int(check_output(["pidof", "-s", "ffmpeg"]))
    if pid is None:
        return False
    os.kill(pid, signal.SIGINT)
    return True
    print("Recording Stopped; Killing ffmpeg")


# ENSURES VIDEO IS KILLED ON CLOSE
def kill_video():

    try:
        outs, errs = HI_Q_process.communicate(timeout=1)
    except TimeoutExpired:
        HI_Q_process.kill()
        outs, errs = HI_Q_process.communicate()
        pass
    try:
        outs, errs = TWOX_ZOOM_process.communicate(timeout=1)
    except TimeoutExpired:
        TWOX_ZOOM_process.kill()
        outs, errs = TWOX_ZOOM_process.communicate()
        pass
    try:
        outs, errs = VIDEO_WITH_AUDIO_process.communicate(timeout=1)
    except TimeoutExpired:
        VIDEO_WITH_AUDIO_process.kill()
        outs, errs = VIDEO_WITH_AUDIO_process.communicate()
        pass
    try:
        outs, errs = AUDIO_ONLY_process.communicate(timeout=1)
    except TimeoutExpired:
        AUDIO_ONLY_process.kill()
        outs, errs = AUDIO_ONLY_process.communicate()
        pass


# RAISES CONSOLE FRAME AFTER FRAME ON TOP CLOSES
def raise_console():
    system_frame_left.tkraise()


# RAISE VIDEO FRAME
def raise_video():
    VIDEO_FRAME.tkraise()


# DESTROYS VIDEO FRAME
def video_destroy():
    VIDEO_FRAME.destroy()


# ATTACHED TO VOLUME SLIDER / ADD LIBRARY TO CONTROL MPV VOLUME
def volume(x):
    pass


# SHUTDOWN/REBOOT MESSAGE BOX
def reboot_shutdown_popup():
    global pop
    pop = tk.Toplevel(system_frame_left)
    pop.title("My Popup")
    pop.geometry("250x150")
    pop.config(bg="#514d7e")
    reb_shutdown_frame = Frame(pop,)
    reb_shutdown_frame.pack(expand=TRUE, fill=BOTH)
    REBOOT = Button(reb_shutdown_frame, text="Reboot", command=lambda: reb_shut_choice("REBOOT"))
    REBOOT.pack(side=LEFT, expand=TRUE,  fill=BOTH)
    SHUTDOWN = Button(reb_shutdown_frame, text="Shutdown", command=lambda: reb_shut_choice("SHUTDOWN"))
    SHUTDOWN.pack(side=RIGHT, expand=TRUE, fill=BOTH)


# KILLS TMUX AT PROGRAM CLOSE -- ADDED AFTER MAINLOOP
def KILL_TMUX():
    subprocess.call('tmux kill-server', shell=True)


# TERMINAL RADIO BUTTONS
LOCAL_SHELL_TOGGLE = Radiobutton(root, text="Local Shell", variable=var, value=1, command=tmux_local_term_swap)
LOCAL_SHELL_TOGGLE.place(x=353, y=548)

REMOTE_SHELL_TOGGLE = Radiobutton(root, text="Remote Shell", variable=var, value=2, command=tmux_remote_term_swap)
REMOTE_SHELL_TOGGLE.place(x=560, y=548)

Pex_Log = Radiobutton(root, text="Pex Log", variable=var, value=3)
Pex_Log.place(x=155, y=548)


# BUTTONS
# ----------------------------------


FFMPEG_BUTTON = tk.Button(system_frame_bottom, bd=0, command=FFMPEG_LOG)
FFMPEG_button_load = Image.open('./Images/TKinter_Buttons/FFMPEG_LOG.png')
FFMPEG_LOG_img = ImageTk.PhotoImage(FFMPEG_button_load)
FFMPEG_BUTTON.config(image=FFMPEG_LOG_img)
FFMPEG_BUTTON.grid(row=5, column=0, pady=(0, 0), padx=(0, 0), sticky="")

SIGNAL_BUTTON = tk.Button(system_frame_bottom, bd=0, command=test_signal)
TEST_SIGNAL_button_load = Image.open('./Images/TKinter_Buttons/TEST_SIGNAL.png')
TEST_SIGNAL_img = ImageTk.PhotoImage(TEST_SIGNAL_button_load)
SIGNAL_BUTTON.config(image=TEST_SIGNAL_img)
SIGNAL_BUTTON.grid(row=6, column=0, pady=(0, 0), padx=(0, 0), sticky="")

RTSP_BUTTON = tk.Button(system_frame_bottom, bd=0, command=RTSP_LOG)
RTSP_LOG_button_load = Image.open('./Images/TKinter_Buttons/RTSP_LOG.png')
RTSP_LOG_img = ImageTk.PhotoImage(RTSP_LOG_button_load)
RTSP_BUTTON.config(image=RTSP_LOG_img)
RTSP_BUTTON.grid(row=5, column=1, pady=(0, 0), padx=(0, 0), sticky="")

WIFI_CONNECT_BUTTON = tk.Button(system_frame_bottom, bd=0, command=wifi_connect)
WIFI_CONNECT_button_load = Image.open('./Images/TKinter_Buttons/WIFI_CONNECT.png')
WIFI_CONNECT_img = ImageTk.PhotoImage(WIFI_CONNECT_button_load)
WIFI_CONNECT_BUTTON.config(image=WIFI_CONNECT_img)
WIFI_CONNECT_BUTTON.grid(row=6, column=1, pady=(0, 0), padx=(0, 0))

HTOP_BUTTON = tk.Button(system_frame_bottom, bd=0, command=HTOP)
HTOP_button_load = Image.open('./Images/TKinter_Buttons/HTOP.png')
HTOP_img = ImageTk.PhotoImage(HTOP_button_load)
HTOP_BUTTON.config(image=HTOP_img)
HTOP_BUTTON.grid(row=5, column=2, pady=(0, 0), padx=(0, 0))

CONSOLE_BUTTON = tk.Button(system_frame_bottom, bd=0, command=show_console)
CONSOLE_button_load = Image.open('./Images/TKinter_Buttons/CONSOLE.png')
CONSOLE_img = ImageTk.PhotoImage(CONSOLE_button_load)
CONSOLE_BUTTON.config(image=CONSOLE_img)
CONSOLE_BUTTON.grid(row=6, column=2, pady=(0, 0), padx=(0, 0))

KILL_STREAM_BUTTON = tk.Button(system_frame_bottom, bd=0, command=kill_stream)
KILL_STREAM_button_load = Image.open('./Images/TKinter_Buttons/KILL_STREAM.png')
KILL_STREAM_img = ImageTk.PhotoImage(KILL_STREAM_button_load)
KILL_STREAM_BUTTON.config(image=KILL_STREAM_img)
KILL_STREAM_BUTTON.grid(row=5, column=3, pady=(0, 0), padx=(0, 0))

REBOOT_SHUTDOWN_BUTTON = tk.Button(system_frame_bottom, bd=0, command=reboot_shutdown_popup)
REBOOT_SHUTDOWN_button_load = Image.open('./Images/TKinter_Buttons/REBOOT_SHUTDOWN.png')
REBOOT_SHUTDOWN_img = ImageTk.PhotoImage(REBOOT_SHUTDOWN_button_load)
REBOOT_SHUTDOWN_BUTTON.config(image=REBOOT_SHUTDOWN_img)
REBOOT_SHUTDOWN_BUTTON.grid(row=6, column=3, pady=(0, 0), padx=(0, 0), sticky="NE")


Hi_Q_BUTTON = tk.Button(system_frame_right, command=Hi_Q, bd=0)
HI_Q_button_load = Image.open('./Images/TKinter_Buttons/HI_Q.png')
HI_Q_img = ImageTk.PhotoImage(HI_Q_button_load)
Hi_Q_BUTTON.config(image=HI_Q_img)
Hi_Q_BUTTON.grid(row=0, column=4, pady=(0, 0), padx=(0, 0))

TWOX_ZOOM_BUTTON = tk.Button(system_frame_right, command=TWOX_ZOOM, bd=0)
TWOX_ZOOM_button_load = Image.open('./Images/TKinter_Buttons/2X_ZOOM.png')
TWOX_ZOOM_img = ImageTk.PhotoImage(TWOX_ZOOM_button_load)
TWOX_ZOOM_BUTTON.config(image=TWOX_ZOOM_img)
TWOX_ZOOM_BUTTON.grid(row=1, column=4, pady=(0, 0), padx=(0, 0))

VIDEO_WITH_AUDIO_BUTTON = tk.Button(system_frame_right, command=VIDEO_WITH_AUDIO, bd=0)
VIDEO_WITH_AUDIO_button_load = Image.open('./Images/TKinter_Buttons/LOW_Q_AUDIO.png')
VIDEO_WITH_AUDIO_img = ImageTk.PhotoImage(VIDEO_WITH_AUDIO_button_load)
VIDEO_WITH_AUDIO_BUTTON.config(image=VIDEO_WITH_AUDIO_img)
VIDEO_WITH_AUDIO_BUTTON.grid(row=2, column=4, pady=(0, 0), padx=(0, 0))

AUDIO_ONLY_BUTTON = tk.Button(system_frame_right, command=AUDIO_ONLY, bd=0)
AUDIO_ONLY_button_load = Image.open('./Images/TKinter_Buttons/AUDIO_ONLY.png')
AUDIO_ONLY_img = ImageTk.PhotoImage(AUDIO_ONLY_button_load)
AUDIO_ONLY_BUTTON.config(image=AUDIO_ONLY_img)
AUDIO_ONLY_BUTTON.grid(row=3, column=4, pady=(0, 0), padx=(0, 0))

NIGHTVISION_BUTTON = tk.Button(system_frame_right, command=NIGHTVISION, bd=0)
NIGHTVISION_button_load = Image.open('./Images/TKinter_Buttons/NIGHTVISION.png')
NIGHTVISION_img = ImageTk.PhotoImage(NIGHTVISION_button_load)
NIGHTVISION_BUTTON.config(image=NIGHTVISION_img)
NIGHTVISION_BUTTON.grid(row=4, column=4, pady=(0, 0), padx=(0, 0))


# SLIDERS
# ----------------------------------


VOLUME_SLIDER = Scale(root, from_=0, to=100, width=20, length=215, orient=HORIZONTAL)
VOLUME_SLIDER.place(x=857, y=575)
VOLUME_SLIDER.set(100)


# ADD FUNCTIONS IN FUTURE TO CONTROL CONTRAST, BRIGHTNESS, SATURATION SLIDERS
CONTRAST_SLIDER = Scale(root, from_=100, to=0, width=20, length=125, orient=VERTICAL)
CONTRAST_SLIDER.place(x=860, y=438)
CONTRAST_SLIDER.set(50)

BRIGHTNESS_SLIDER = Scale(root, from_=100, to=0, width=20, length=125, orient=VERTICAL)
BRIGHTNESS_SLIDER.place(x=932, y=438)
BRIGHTNESS_SLIDER.set(50)

SATURATION_SLIDER = Scale(root, from_=100, to=0, width=20, length=125, orient=VERTICAL)
SATURATION_SLIDER.place(x=1005, y=438)
SATURATION_SLIDER.set(50)


# ATTACHED TO RECORD BUTTON
RECORD_BUTTON = Button(root, command=start_recording, bd=0)
record_img = ImageTk.PhotoImage(Image.open("./Images/TKinter_Buttons/RECORD-80X80.png"))
RECORD_BUTTON.config(image=record_img)
RECORD_BUTTON.place(x=975, y=630)

# ATTACHED TO STOP BUTTON
STOP_RECORD_BUTTON = Button(root, bd=0, command=stop_recording)
stop_img = ImageTk.PhotoImage(Image.open("./Images/TKinter_Buttons/STOP-RECORD-80X80.png"))
STOP_RECORD_BUTTON.config(image=stop_img)#
STOP_RECORD_BUTTON.place(x=875, y=630)


# MAINLOOP INIT
if __name__ == "__main__":
    os.setpgrp()  # create main group kill child processes
    try:
        rxvt()  # RUN CONSOLE
        root.mainloop()
    finally:
        KILL_TMUX()  # Terminates TMUX sessions
        os.killpg(0, signal.SIGKILL)  # kill all processes in main process group
