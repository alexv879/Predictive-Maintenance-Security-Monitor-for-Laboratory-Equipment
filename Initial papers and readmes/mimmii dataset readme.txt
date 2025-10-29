https://zenodo.org/records/3384388

MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection
Creators
Purohit, Harsh1
 
Excellent question. You've hit on a key part of working with large datasets: being strategic about what you download to save time and disk space.

No, you do not need to download all of them to start.

For your MVP, you should follow the lean principle of starting with the smallest dataset that can prove your concept. The different dB levels represent different signal-to-noise ratios, which is how much background noise is mixed in with the machine sound.

Here is my specific recommendation for Phase 1, Week 1:

1. Start with One Machine Type and the Cleanest Data.
The best place to start is with the cleanest, most representative data.

Download this file first: 0_dB_fan.zip (10.4 GB)

Why this one?

fan: Fans produce a consistent, steady sound, which makes it an ideal candidate for your first model to learn the difference between "normal hum" and "abnormal clicking/rattling."

0_dB: This represents a "normal" level of background noise. It's not perfectly clean, but it's not excessively noisy. This is the perfect baseline for training your foundational model.

2. What to Do with This File:
Once you download and unzip 0_dB_fan.zip, you will find a directory structure. Inside, you will see folders like train and test.

For Training Your Model: Go into the train folder. Inside, you will find a subfolder named normal. These .wav files are the only ones you need to train your initial acoustic anomaly model.

For Testing Your Model: Go into the test folder. Inside, you will find normal and abnormal subfolders. You will use these files to check how well your trained model performs.

What about the other files?

Think of them as resources for future improvements, once your first model is working.

The other 0_dB files (pump, slider, valve): Once you have a successful model for the fan, you can download these to train models for other machine types, expanding your product's capability.

The -6_dB and 6_dB files: These are for making your model more robust.

The -6_dB files are noisier. You can use them later to test how well your model performs in a loud environment or to retrain it to be better at ignoring background noise.

The 6_dB files are cleaner. They are also good for testing and fine-tuning.

By starting with just 0_dB_fan.zip, you can complete the entire development and testing loop for one specific use case, which is a much faster and more manageable goal.




Tanabe, Ryo1
 
Ichige, Kenji1
 
Endo, Takashi1
 
Nikaido, Yuki1
 
Suefusa, Kaori1
ORCID icon
 
Kawaguchi, Yohei1
ORCID icon
Description
This dataset is a sound dataset for malfunctioning industrial machine investigation and inspection (MIMII dataset). It contains the sounds generated from four types of industrial machines, i.e. valves, pumps, fans, and slide rails. Each type of machine includes seven individual product models*1, and the data for each model contains normal sounds (from 5000 seconds to 10000 seconds) and anomalous sounds (about 1000 seconds). To resemble a real-life scenario, various anomalous sounds were recorded (e.g., contamination, leakage, rotating unbalance, and rail damage). Also, the background noise recorded in multiple real factories was mixed with the machine sounds. The sounds were recorded by eight-channel microphone array with 16 kHz sampling rate and 16 bit per sample. The MIMII dataset assists benchmark for sound-based machine fault diagnosis. Users can test the performance for specific functions e.g., unsupervised anomaly detection, transfer learning, noise robustness, etc. The detail of the dataset is described in [1][2].

This dataset is made available by Hitachi, Ltd. under a Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) license.

A baseline sample code for anomaly detection is available on GitHub: https://github.com/MIMII-hitachi/mimii_baseline/

*1: This version "public 1.0" contains four models (model ID 00, 02, 04, and 06). The rest three models will be released in a future edition.

[1] Harsh Purohit, Ryo Tanabe, Kenji Ichige, Takashi Endo, Yuki Nikaido, Kaori Suefusa, and Yohei Kawaguchi, “MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection,” arXiv preprint arXiv:1909.09347, 2019.

[2] Harsh Purohit, Ryo Tanabe, Kenji Ichige, Takashi Endo, Yuki Nikaido, Kaori Suefusa, and Yohei Kawaguchi, “MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection,” in Proc. 4th Workshop on Detection and Classification of Acoustic Scenes and Events (DCASE), 2019.

Files
-6_dB_fan.zip

Files (100.2 GB)
Name	Size	
-6_dB_fan.zip
md5:f02ae808a58d84b6815b7ec38ff30879 	10.9 GB	 
-6_dB_pump.zip
md5:d20b783a0ff9c93d58f452f98c37b112 	8.2 GB	 
-6_dB_slider.zip
md5:49913eda7d37f182cbf8ed5c984140e0 	8.0 GB	 
-6_dB_valve.zip
md5:fdfaf185fea61b21e11952a070a4ada7 	8.0 GB	 
0_dB_fan.zip
md5:6354d1cc2165c52168f9ef1bcd9c7c52 	10.4 GB	 
0_dB_pump.zip
md5:488748295c3f60b25de07b58fe75b049 	7.9 GB	 
0_dB_slider.zip
md5:4d674c21474f0646ecd75546db6c0c4e 	7.5 GB	 
0_dB_valve.zip
md5:178478eb0d11c79080a35562bfdeee71 	7.5 GB	 
6_dB_fan.zip
md5:0890f7d3c2fd8448634e69ff1d66dd47 	10.2 GB	 
6_dB_pump.zip
md5:a09ba6060c10fc09cd4c8770213b0b9f 	7.7 GB	 
6_dB_slider.zip
md5:838c2b3441858359c4704ef13a1b27ff 	7.1 GB	 
6_dB_valve.zip
md5:fe5fb7c337cd701b1d31dc641e621892 	6.9 GB	 
Additional details
References
Harsh Purohit, Ryo Tanabe, Kenji Ichige, Takashi Endo, Yuki Nikaido, Kaori Suefusa, and Yohei Kawaguchi, "MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection," arXiv preprint arXiv:1909.09347, 2019.
Harsh Purohit, Ryo Tanabe, Kenji Ichige, Takashi Endo, Yuki Nikaido, Kaori Suefusa, and Yohei Kawaguchi, "MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection," in Proc. 4th Workshop on Detection and Classification of Acoustic