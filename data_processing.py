"""
Author: Soufiane CHAMI
File: data_processing.py
Description: converts .dat files to .csv and generates an aggregated dataset.
"""
import os
import glob
import wfdb
import pandas as pd
from tqdm import tqdm


# convert the recordings to .csv and save reco labels
class Generate_csv:

    def __init__(self):
        self.dir = os.getcwd() # should be smth like '/path-to-data-file/data/'
    def get_records(self, fol_path):
        """ To get file paths """
        # There are 3 files for each record
        # *.atr is one of them
        paths = glob.glob(os.path.join(self.dir,'*/*.atr'))
        # Get rid of the extension
        paths = [path[:-4] for path in paths]
        paths.sort()
        return paths


    def constructor(self):
        records = self.get_records(self.dir)
        labels_df = pd.DataFrame()
        signal_id= []
        age=[]
        gender=[]
        date=[]
        fs=[]
        sig_len=[]

        for record in tqdm(records):
            data, labels = wfdb.rdsamp(record)
            data= pd.DataFrame(data, columns =labels['sig_name'])
            data_filename= record + '.csv'
            data.to_csv(data_filename, index=False)
            # parse dict
            signal_id.append('_'.join(record.split('/')[-2:]))
            age.append(int(labels['comments'][0][-2:]))
            gender.append(labels['comments'][1][-4:])
            date.append(labels['comments'][2][10:])
            fs.append(labels['fs'])
            sig_len.append(labels['sig_len'])


        # get the first column signal
        labels_df['signal_id']=signal_id
        labels_df['person_id']=['_'.join(c.split('_')[:-2]) for c in signal_id]
        labels_df['rec_id']=['_'.join(c.split('_')[-2:]) for c in signal_id]
        labels_df['age']=age
        labels_df['gender']=gender
        labels_df['date']=date
        labels_df['fs']=fs
        labels_df['sig_len']=sig_len

        lebels_filename= os.path.join('/'.join(record.split('/')[:-2]),'labels.csv')
        print('saved to', lebels_filename)
        labels_df.to_csv(lebels_filename, index=False)

        return # labels_df  #optional return

#generates features and labels
class ProcessData:
    def __init__(self):
        self.dir = os.path.join(os.getcwd(), 'data')
        self.persons_labels = [] #who the person is
        self.age_labels = []     #age of thatperson
        self.gender_labels = []  #is that person male or female
        self.date_labels = []    #month.day.year of ecg record
        self.ecg_filsignal = pd.DataFrame() #filtered ecg dataset
        self.ecg_signal = pd.DataFrame()  #unfiltered ecg dataset

  #extracts labels and features from rec_1.hea of each person
    def extract_labels(self, filepath):
        for folders in os.listdir(filepath):
            if (folders.startswith('Person_')):
                self.persons_labels.append(folders)
            for inpersonsdir in os.listdir(os.path.join(filepath, folders)):
              if (inpersonsdir.startswith('rec_1.') and inpersonsdir.endswith('hea')):
                  with open(os.path.join(filepath, folders, inpersonsdir),"r") as f:
                    array2d = [[str(token) for token in line.split()] for line in f]
                    self.age_labels.append(array2d[4][2])
                    self.gender_labels.append(array2d[5][2])
                    self.date_labels.append(array2d[6][3])
                  f.close()

  #extract features from rec_1.csv of each person
  def extract_feats(self, filepath):
    p = 0 #person counter
    global f_num
    f_num = 0 #file counter
    for folders in os.listdir(filepath):
      if (folders.startswith('Person_')):
        p = p + 1
        for files in os.listdir(os.path.join(filepath, folders)):
          if (files.endswith('csv')):
           with open(os.path.join(filepath, folders, files), "r") as x:
              f_num = f_num + 1
              features = pd.read_csv(x, header=[0,1])
              pdfeats = pd.DataFrame(features)
              pdfeats = pdfeats.apply(pd.to_numeric)
              temp = [p] #0th index is person_label int
              temp1 = [p]
              for rows in range(len(pdfeats)):
                temp.append(pdfeats.get_value(rows, 1, True))
                temp1.append(pdfeats.get_value(rows, 0, True))
              tempnp = np.asarray(temp, dtype=float)
              if (tempnp.shape == (9999,)):
                tempnp = np.append(tempnp, tempnp[9998])
              temp1np = np.asarray(temp1, dtype=float)
              if (temp1np.shape == (9999,)):
                temp1np = np.append(temp1np, tempnp[9998])
              self.dumpfeats(tempnp,1)
              self.dumpfeats(temp1np,2)
           x.close()

  #appends to a bigger global array
  def dumpfeats(self, array, flag):
    fil_df = pd.DataFrame(array)
    fil_df = fil_df.T
    ufil_df = pd.DataFrame(array)
    ufil_df = ufil_df.T
    if (flag == 1):
      self.ecg_filsignal = self.ecg_filsignal.append(fil_df, ignore_index=True)
    if (flag == 2):
      self.ecg_signal = self.ecg_signal.append(ufil_df, ignore_index=True)

  def init(self):
    print("Setting up DeepECG data labels..")
    self.extract_labels(self.dir)
    ecglabels = [list(i) for i in zip(self.persons_labels,self.age_labels,self.gender_labels,self.date_labels)]
    print("Exporting labels to csv..")
    df_ecglabels = pd.DataFrame(ecglabels)
    df_ecglabels.to_csv(os.path.join('processed_data', 'ecgdblabels.csv'), index=False)
    print("Export complete.")

    print("Setting up DeepECG data features..")
    self.extract_feats(self.dir)
    print("Exporting feature set to csv..")
    self.ecg_filsignal.to_csv(os.path.join('processed_data', 'filecgdata.csv'), index=False)
    self.ecg_signal.to_csv(os.path.join('processed_data', 'unfilecgdata.csv'), index=False)
    print("Export complete.")

    if(os.path.isfile(os.path.join('processed_data', 'filecgdata' + "." + 'csv')) and os.path.isfile(os.path.join('processed_data', 'unfilecgdata' + "." + 'csv'))):
      print("Data in processed_data/ folder is now ready for training.")

#aligns dataset by first max peak
class Augmentation:
  def __init__(self):
    self.maxs = []
    self.mins = []
    self.aligned_data = pd.DataFrame()
    self.new_data = pd.DataFrame()
    self.rsampled_data = pd.DataFrame()
    self.person_tab = []

  #helper functions
  def peak_maxhelper(self, array):
    self.peakdet(array, 0.5, flag='max')

  #returns lists of maxvalues and maxpositions
  def peaks_perperson(self, ndnp, row, maxarr):
    #mv = ndnp[row][:]
    maxpositions = maxarr[row][:, np.r_[0:1]].ravel()
    #maxvalues = maxarr[row][:,1].ravel()
    return maxpositions

  #peak detector
  def peakdet(self, v, delta, flag, x=None):
    maxtab = [] #[(max_pos, max)..]
    mintab = [] #[(min_pos, min)..]
    if x is None:
      x = np.arange(len(v))
    v = np.asarray(v)
    if len(v) != len(x):
      sys.exit('Input vectors v and x must have same length')
    if not np.isscalar(delta):
      sys.exit('Input argument delta must be a scalar')
    if delta <= 0:
      sys.exit('Input argument delta must be positive')

    mn, mx = Inf, -Inf
    mnpos, mxpos = np.NaN, np.NaN

    lookformax = True

    for i in np.arange(len(v)):
      this = v[i]
      if this > mx:
        mx = this
        mxpos = x[i]
      if this < mn:
        mn = this
        mnpos = x[i]
      if lookformax:
        if this < mx-delta:
          maxtab.append((mxpos, mx))
          mn = this
          mnpos = x[i]
          lookformax = False
      else:
        if this > mn+delta:
          mintab.append((mnpos, mn))
          mx = this
          mxpos = x[i]
          lookformax = True
    if flag is 'max':
      npmaxtab = np.asarray(maxtab)
      self.maxs.append(npmaxtab)
    if flag is 'min':
      npmintab = np.asarray(mintab)
      self.mins.append(npmintab)

  #calls slice signal on consequitive pairs of max peaks
  def helper_slice(self, ndnp, personid, row, maxdist, maxarr, maxpos):
    #print row
    for curr_pos, next_pos in zip(maxpos, islice(maxpos,1,None)):
      self.slice_signal(ndnp, personid, row, maxdist, curr_pos, next_pos)

  #splits data into peak to peak chunks
  def slice_signal(self, ndnp, personid, row, maxdist, start, stop):
    global new_data
    mv = ndnp[row][:]
    step_back = stop-1
    chunk = mv[start:step_back]
    #normal heart rate: 50 to 140 beats per minute
    #choose 70 as our typical beats per minute
    #60/70 * 500 = 428.57 ~ 430
    rchunk = signal.resample(chunk, 430) #resample chunk
    temp = np.asarray([personid])
    chunktab = np.concatenate((temp, rchunk), axis=0)
    self.gen_dataset(chunktab, personid, 'resampled')

  #aligns all signals by first peak
  def align_data(self, ndnp, personid, row, first_peak):
    mv = ndnp[row][:]
    chunk = mv[first_peak:]
    self.gen_dataset(chunk, personid, 'align')

  #appends chunk to a global nd array
  def gen_dataset(self, array, personid, flag):
    chunk_df = pd.DataFrame(array)
    chunk_df = chunk_df.T

    if flag is 'align':
      self.aligned_data = self.aligned_data.append(chunk_df, ignore_index=True)
      self.person_tab.append(personid)
      #print personid, person_tab

    if flag is 'new':
      self.new_data = self.new_data.append(chunk_df, ignore_index=True)

    if flag is 'resampled':
      #print "in gen dataset"
      self.rsampled_data = self.rsampled_data.append(chunk_df, ignore_index=True)

  #distance b/w two points
  def dist(self, p1, p2):
    (x1, y1), (x2, y2) = p1, p2
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)

  def init(self):
    data = pd.read_csv(os.path.join('processed_data', 'filecgdata.csv'))
    npdata = np.asarray(data)

    personid = npdata[:,0]
    signals = npdata[:,np.r_[1:10000]]

    #1. detect peaks of signals
    np.apply_along_axis(self.peak_maxhelper, 1, signals)
    maxnp = np.asarray(self.maxs)

    #2. find distance between max peaks
    #we resample signals by maxdist after slicing
    dfmaxs = pd.DataFrame(maxnp)
    for row in range(len(dfmaxs)):
      dists = [self.dist(p1,p2) for p1, p2 in combinations(dfmaxs.get_value(row,0,True), 2)]
    npdist = np.asarray(dists) #list of distances
    maxdist = np.amax(npdist) #max distance between two peaks
    #print int(maxdist) #maxdist = 9077

    #3. align dataset by first peak
    print("generating aligned dataset ...")
    for i, row in enumerate(signals):
      amax = np.amax(row)
      if (amax < 0.5): continue
      max_pos = self.peaks_perperson(signals, i, maxnp)
      first_max = max_pos[0]
      self.align_data(signals, personid[i], i, int(first_max))

    np_aligned = np.asarray(self.aligned_data)

    #4. slice the data peak to peak and resample to maintain width/num.of.samples
    slice_resample = True #slice peak to peak and resize data
    if (slice_resample):
      print("slicing and resampling data ...")
      for i, row in enumerate(signals):
        amax = np.amax(row) #get max of signal
        if (amax < 0.5): continue  #if max < threshold, drop signal
        max_pos1 = self.peaks_perperson(signals, i, maxnp)
        self.helper_slice(signals, personid[i], i, int(maxdist), maxnp, max_pos1.astype(np.int64))

      print("exporting dataset ...")
      path = os.path.join('processed_data', 'rsampled_data.csv')
      self.rsampled_data.to_csv(path, index=False)
      print("export complete!")

    # (alternative) 4. slice every 2500 seconds
    # instead of slicing peak to peak. no resampling.
    slice_every2500 = False #slice every 2500 samples
    if (slice_every2500):
      print("slicing data ...")
      for i, row in enumerate(np_aligned):
          split_arr = np.array_split(row, 4)
          for j in np.arange(4):
            this = split_arr[j]
            if (np.isnan(this).any() or np.less(len(this),2500)):
              continue
            with_label = np.insert(split_arr[j],0,self.person_tab[i]) #prepend personid
            self.gen_dataset(with_label, self.person_tab[i], 'new')

      print("exporting dataset ...")
      path = os.path.join('processed_data', 'new_data.csv')
      self.new_data.to_csv(path, index=False)
      print("export complete!")

#sets up the data for training and testing
class Setup():
  def __init__(self):
    self.p_labels = self.a_labels = self.g_labels = np.array([], dtype=np.int32)
    self.train_d = self.test_d = self.train_l = self.test_l = np.array([])
    self.people = self.age = self.gender = self.date = np.array([])
    self.p = np.arange(90)

  def get_data(self):
    #read features from csv files
    new_data = pd.read_csv(os.path.join('processed_data', 'rsampled_data.csv'))
    data = pd.DataFrame(new_data)
    npdata = np.asarray(data, dtype=np.float32) #changed from 64 to 32
    personid = npdata[:,0] #strip labels
    feats = npdata[:, np.r_[1:431]] #strip features

    ecglabels = pd.read_csv(os.path.join('processed_data', 'ecgdblabels.csv'))
    pdlabels = pd.DataFrame(ecglabels)
    labels = np.asarray(pdlabels)
    return feats, personid.astype(int), labels

  #splits data for training and testing
  def split_data(self, np_feats, np_labels):
    self.train_d = np_feats[np.r_[0:651],:]
    self.test_d = np_feats[np.r_[651:729],:]
    self.train_l = np_labels[np.r_[0:651]]
    self.test_l = np_labels[np.r_[651:729]]
    return self.train_d, self.train_l, self.test_d, self.test_l

  def random_split(self, np_feats, np_labels):
    self.train_d, self.test_d, self.train_l, self.test_l = train_test_split(
        np_feats, np_labels, test_size=0.10, random_state=42)
    return self.train_d, self.test_d, self.train_l, self.test_l

  #splits the labels into people, age, gender
  def dissect_labels(self, np_labels):
    self.people = np_labels[:, 0]
    self.age = np_labels[:,1]
    self.gender  = np_labels[:,2]
    return self.people, self.age, self.gender

  #people are unique numbers from 0-89 in order
  #age from dtype obj to ints
  #gender from dtype obj to int 0 for m, 1 for f
  def labels_to_ints(self, people, age, gender):
    for gen in gender:
      if (gen == 'male'):
        self.g_labels = np.append(self.g_labels, 0)
      if (gen == 'female'):
        self.g_labels = np.append(self.g_labels, 1)
    return people, age, self.g_labels

#gets data from Setup() in the form required
class getData():
  def __init__(self):
    self.people_labels = self.age_labels = self.gender_labels = np.array([])
    self.x_train = self.y_train = self.x_test = self.y_test = np.array([])
    self.id_gender = [] #gender labels for new dataset

  def get(self):
    inst = Setup()
    feats, personid, info = inst.get_data()
    p, a, g = inst.dissect_labels(info)
    self.people_labels, self.age_labels, self.gender_labels = inst.labels_to_ints(p, a, g)
    X, Y = self.gender_id(feats, personid)
    return X, Y, p
    #comment out line 368-369 for person identification
    #uncomment the line below
    #self.split_dataset(feats, personid)

  def gender_id(self, feat, personid):
    for i, person in enumerate(personid):
      this = self.gender_labels[int(person)-1]
      self.id_gender.append(this)
    return feat, np.asarray(self.id_gender, dtype=np.int32) #for k_fold
    #self.split_dataset(feat, self.id_gender)

  def split_dataset(self, feat, labels):
    inst = Setup()
    self.X_train, self.X_test, self.Y_train, self.Y_test = inst.random_split(np.asarray(feat, dtype=np.float), np.asarray(labels, dtype=np.int32))

class plotHelper():
  # prints and plots the confusion matrix
  def plot_confusion_matrix(cm, classes, title='Confusion matrix', cmap=plt.cm.Blues):
      print(cm)
      plt.imshow(cm, interpolation='nearest', cmap=cmap)
      plt.title(title)
      plt.colorbar()
      tick_marks = np.arange(len(classes))
      plt.xticks(tick_marks, classes, rotation=45)
      plt.yticks(tick_marks, classes)

      fmt = 'd'
      thresh = cm.max() / 2.
      for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
          plt.text(j, i, format(cm[i, j], fmt),
                   horizontalalignment="center",
                   color="white" if cm[i, j] > thresh else "black")

      plt.tight_layout()
      plt.ylabel('True label')
      plt.xlabel('Predicted label')
      plt.show()

  # summarise history for accuracy and loss graphically
  def plot_keys(history):
      print(history.history.keys())
      plt.plot(history.history['acc'])
      plt.plot(history.history['val_acc'])
      plt.title('model accuracy')
      plt.ylabel('accuracy')
      plt.xlabel('epoch')
      plt.legend(['train', 'test'], loc='upper left')
      plt.show()
      plt.plot(history.history['loss'])
      plt.plot(history.history['val_loss'])
      plt.title('model loss')
      plt.ylabel('loss')
      plt.xlabel('epoch')
      plt.legend(['train', 'test'], loc='upper left')
      plt.show()

#call methods unless already called
if(os.path.isfile(os.path.join('processed_data', 'filecgdata' + "." + 'csv'))
and os.path.isfile(os.path.join('processed_data', 'unfilecgdata' + "." + 'csv'))
and os.path.isfile(os.path.join('processed_data', 'ecgdblabels' + "." + 'csv'))
and os.path.isfile(os.path.join('processed_data', 'new_data' + "." + 'csv'))
and os.path.isfile(os.path.join('processed_Data', 'rsampled_data' + "." + 'csv'))):
  pass
else:
  #convert all .dat files to .csv
  generate = csvGenerator()
  generate.tocsv()

  #create an aggregated dataset
  processing = ProcessData()
  processing.init()

  #align data by first max peak
  aligndata = Augmentation()
  aligndata.init()
