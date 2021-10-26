from pydicom import *

class RangeShifter:
    '''
        Add or modify range shifter tags in an existing dicom file
        
        Choose whether to add a range shifter or modify an existing range shifter.
        Adding a range shifter: RS thickness and snout position arguments are required
        Existing range shifter: RS thickness and snout position are both optional
        
        Args:
            infile (str): name of dicom file to be modified
            plan_id (str): Modified file's RT Plan Label
            snout_position (float or int): Snout position in mm. Must be between 20.0 and 421.0 when adding a range shifter
            range_shifter (int): Range shifter thickness in cm. Must be either 2, 3, or 5 when adding a range shifter
            outfile (str): Optional modified dicom file name
            add_rangeshifter (bool): True if adding a range shifter. False is modifying an existing range shifter
            
        Functions:
            add(): adds or modifies range shifter attributes in infile
            save(): saves modified dicom to file
    '''
    def __init__(self,
        infile,
        plan_id,
        snout_position=None,
        range_shifter=None,
        outfile=None,
        add_rangeshifter=True,
        ):

        if not isinstance(infile, str):
            raise TypeError("infile must be a string")
        elif not infile[-4:] == '.dcm':
            raise ValueError("infile must include .dcm file extension")
        
        if range_shifter in [2,3,5]:
            self.RangeShifterID = "RS="+str(range_shifter)+"cm"
        elif add_rangeshifter and not range_shifter in [2,3,5]:
            raise ValueError("range_shifter must be int, either: 2, 3 or 5")
        elif not add_rangeshifter and not range_shifter in [2,3,5,None]:
            raise ValueError("range_shifter must be None or int (either: 2, 3 or 5)")
        
        if not isinstance(plan_id, str):
            raise TypeError("plan_id must be a string")
        
        if add_rangeshifter and not isinstance(snout_position,(float,int)):
            raise TypeError("snout_position must be float or int")
        elif add_rangeshifter and (snout_position>421.0 or snout_position<20.0):
            raise ValueError("snout_position must be between 20.0 and 421.0")
        elif not add_rangeshifter and (snout_position>421.0 or snout_position<20.0 or snout_position==None):
            raise ValueError("snout_position must be None or between 20.0 and 421.0")
            
        if outfile is None:
            self.outfile = infile[:-4]+"_RS"+str(range_shifter)+"_Snout"+str(snout_position)+".dcm"
        else:
            if not outfile[-4:] == '.dcm':
                outfile = outfile+'.dcm'
            self.outfile = outfile
        
        # set range shifter defaults
        max_rs_rad = 461.0
        max_snout_rad = 421.0
        if snout_position:
            self.IsocentertoRangeShifterDistance = max_rs_rad-max_snout_rad+snout_position
        
        self.infile = infile
        self.RTPlanLabel = plan_id
        self.SnoutPosition = snout_position
        self.add_rangeshifter = add_rangeshifter   
        self.RangeShifterNumber = 1
        self.ReferencedRangeShifterNumber = 1
        self.RangeShifterType = "BINARY"
        self.RangeShifterSetting = "IN"
        self.NumberOfRangeShifters = 1            
        self.RangeShifterWaterEquivalentThickness = 23.0
        
        
    def add(self):
        '''
            Add or modify a range shifter to the dicom file
        '''
        
        # load dicom file
        ds=dcmread(self.infile)
        
        if self.add_rangeshifter == True: # create new range shifter
            # range shifter sequence (300a,0314)
            rs_seq = Dataset()
            rs_seq.RangeShifterNumber = self.RangeShifterNumber
            rs_seq.RangeShifterID = self.RangeShifterID
            rs_seq.RangeShifterType = self.RangeShifterType
            
            # range shifter settings sequence (300a,0360)
            rs_set_seq = Dataset()
            rs_set_seq.RangeShifterSetting = self.RangeShifterSetting
            rs_set_seq.IsocenterToRangeShifterDistance = self.IsocentertoRangeShifterDistance
            rs_set_seq.RangeShifterWaterEquivalentThickness = self.RangeShifterWaterEquivalentThickness
            rs_set_seq.ReferencedRangeShifterNumber = self.ReferencedRangeShifterNumber
    
            # modify dicom file
            for ion_beam_seq in ds.IonBeamSequence:
                ion_beam_seq.NumberOfRangeShifters = self.NumberOfRangeShifters
                ion_beam_seq.IonControlPointSequence[0].SnoutPosition = self.SnoutPosition
                ion_beam_seq.RangeShifterSequence = Sequence([rs_seq])
                ion_beam_seq.IonControlPointSequence[0].RangeShifterSettingsSequence = Sequence([rs_set_seq])

        else: # modify existing range shifter
            # modify dicom file
            for ion_beam_seq in ds.IonBeamSequence:
                if self.RangeShifterID:
                    RangeShifterSequence = ion_beam_seq.RangeShifterSequence
                    RangeShifterSequence[0].RangeShifterID = RangeShifterID
                if self.SnoutPosition:
                    ion_beam_seq.IonControlPointSequence[0].SnoutPosition = self.SnoutPosition
                    RangeShifterSettingsSequence = ion_beam_seq.IonControlPointSequence[0].RangeShifterSettingsSequence
                    RangeShifterSettingsSequence[0].IsocenterToRangeShifterDistance = self.IsocentertoRangeShifterDistance
        
        # update metadata tags
        ds.RTPlanLabel = self.RTPlanLabel
        uid = ds.SOPInstanceUID
        ds.SOPInstanceUID = uid[0:2]+'4'+uid[3:]
        print("Modified Plan File: "+self.outfile+", Plan ID: "+self.RTPlanLabel+", UID: "+uid[0:2]+'4'+uid[3:])
        self.ds = ds
        
    
    def save(self):
        '''
            Save modified dicom to file
        '''
        ds = self.ds
        ds.save_as(self.outfile)
        

        
        