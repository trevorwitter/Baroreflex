from pandas import DataFrame 
import pandas as pd
import numpy as np
from numpy import diff
from scipy.stats import linregress
from scipy.signal import butter, lfilter, freqz
import matplotlib.pyplot as plt

df = pd.read_csv('/Users/twitter/Desktop/Python Projects/Sample Data/Sample_ECG5.txt', delimiter = "\t", index_col=0)
frame = DataFrame(df)

frame.index.names = ['time']
df.columns=['ecg', 'bp']

#Low pass filter for ECG signal
def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

Filtered_ECG = butter_lowpass_filter(frame['ecg'], 3.667, 1000.0, order=5)

# Filter requirements.
order = 6
fs = 30.0       # sample rate, Hz
cutoff = 3.667  # desired cutoff frequency of the filter, Hz

# Get the filter coefficients so we can check its frequency response.
b, a = butter_lowpass(cutoff, fs, order)

frame['filtered_ecg']= Filtered_ECG


#QRS threshold 
threshold = (np.max(frame.filtered_ecg) - (np.max(frame.filtered_ecg)-np.min(frame.filtered_ecg))*.2)

#QRS detection
ind = 0
ind2 = 0
hbindex = [frame.index[0]]
heartbeat = []
RRindex = []
hbs = [0]
timestamp = []
for x in Filtered_ECG:
    ind += 1
    if x > threshold and Filtered_ECG[ind-1] > Filtered_ECG[(ind-1)-1] and Filtered_ECG[ind-1] > Filtered_ECG[(ind-1)+1]:       #Threshold on frame ecg works
        ind2 += 1
        hbs.append(ind2)
        heartbeat.append(ind2)
        hbindex.append(frame.index[ind]) #timestamp for all detectected QRS in ECG
    else:
        heartbeat.append(ind2)

frame['heart_beat'] = heartbeat

#Heart Rate
RR = np.diff(hbindex)
HR = 60/RR
RR[0] = RR[1]
HR[0] = HR[1]

#beat to beat BP values for each QRS
sbp = []
mbp = []
dbp = []
for x in hbs:
    sbp.append(np.max(frame[frame.heart_beat == x].bp))
    mbp.append(np.mean(frame[frame.heart_beat == x].bp))
    dbp.append(np.min(frame[frame.heart_beat == x].bp))

print frame 

#Output dataframe
frame2 = DataFrame(hbs[1:], columns = ['hb'])
frame2['time'] = hbindex[1:]
frame2['RR'] = RR
frame2['HR'] = HR
frame2['sbp'] = sbp[1:]
frame2['mbp'] = mbp[1:]
frame2['dbp'] = dbp[1:]

#Binning by SBP
BPbin= []
for y in frame2.sbp:
    BPbin.append(int((y - min(frame2.sbp))/3))
frame2['bin'] = BPbin
frame2 = frame2[:(len(frame2))-2] #removes trailing incomplete cardiac cycle
print frame2

groupedRR = frame2['RR'].groupby(frame2['bin'])
RRarray = groupedRR.mean() 

groupedSBP = frame2['sbp'].groupby(frame2['bin'])
SBParray = np.asarray(groupedSBP.mean())
print SBParray

bin_weight = groupedSBP.size()/frame2['hb'].max()
frame3 = frame2.mean()


#linear regression
#RR vs SBP
slope, intercept, r_value, p_value, std_err = linregress(SBParray, RRarray)
frame3['BRS slope'] = slope
frame3['R^2'] = r_value**2
print frame3
bestfit = [(i*0.012020)+intercept for i in SBParray]

#plots plots plots plots plots plots plots plots plots plots plots
fig = plt.figure()

#ECG plot
ax1 = fig.add_subplot(2, 1, 1)
plt.plot(frame.index, frame.filtered_ecg)
plt.plot(frame2.time, frame.filtered_ecg[frame2.time], linestyle=' ', marker='o')

#blood pressure plot
ax2 = fig.add_subplot(2, 1, 2)
plt.xlabel('Time, s')
plt.plot(frame.index, frame.bp)
plt.plot(frame2.time, frame2.sbp)
plt.plot(frame2.time, frame2.mbp)
plt.plot(frame2.time, frame2.dbp)
plt.ylabel('Blood Pressure')
fig2 = plt.figure()

#correlation plot
#RR vs SBP 
fig3 = plt.figure()
ax4 = fig3.add_subplot(1, 1, 1)
plt.plot(SBParray, RRarray, linestyle=' ', marker='.', color='k') 
plt.ylabel('RR interval')
plt.xlabel('Systolic Blood Pressure')
plt.plot(SBParray, bestfit, marker=' ', linestyle='--', color='k')
plt.xlim(117, 144)
plt.text(119, 1.08, r'$Slope = %s,\ R^2=%s$' % (np.round(slope, decimals = 2), np.round(frame3['R^2'], decimals = 2)))

plt.show()
