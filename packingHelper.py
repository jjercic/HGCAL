import numpy as np


###############################################################
### Functions for packing and unpacking data to wanted format
###############################################################

def pack4E4M_FromInt(energy): #Take input integer and pack it into 4E4M format
    assert(energy<0x80000);#make sure input is an 19 bit number

    if(energy<16): #here the max number is 16 because mantissa has 4 bits, 2^4=16
        return int(energy)
    e = 1
    while(energy>=32):
        e+=1
        energy>>=1
    return int(16*(e-1)+energy) #format it in as 16 bits = eeeemmm, where first 4 are exponent and last 4 are (mantissa - 16)

def unpack4E4M_ToInt(num): #Take 4E4M as input and unpack it to integer
    assert(num<0x100);#make sure input is an 8 bit number

    e = ((num>>4)&0x0f);#Read first 4 bits from the input number to read the exponent
    m = ((num   )&0x0f);#Read the last 4 bits as mantissa
    #print(e,m)

    if(e==0):
        return m
    elif(e==1):
        return 16+m
    else:
        return (32+2*m+1)<<(e-2)#Recover the fact that this is (mantissa - 8), take into account first multiplication with 2 inside the bracket and then shift to right e-2 time which is equivalent to multiplying by 2

def pack5E3M_FromInt(energy): #Take 5E3M format and unpack it into intiger
    assert(energy<0x400000000);#make sure input is an 34 bit number

    if(energy<8): #here the max number is 8 because mantissa has 3 bits, 2^3=8
        return int(energy)
    e = 1
    while(energy>=16):
        e+=1
        energy>>=1
    #print(e,energy)
    return int(8*(e-1)+energy) #format it in as 8 bits = eeeeemmm, where first 5 are exponent and last 3 are (mantissa - 8)

def unpack5E3M_ToInt(num): #Take intiger as input and pack it into 5E3M format
    assert(num<0x100);#make sure input is an 8 bit number

    e = ((num>>3)&0x1f);#Read first 5 bits from the input number to read the exponent
    m = ((num   )&0x07);#Read the last 3 bits as mantissa
    #print(e,m)

    if(e==0):
        return m
    elif(e==1):
        return 8+m
    else:
        return (16+2*m+1)<<(e-2)#Recover the fact that this is mantissa - 8, take into account first multiplication with 2 inside the bracket and then shift to right e-2 time which is equivalent to multiplying by 2

def pack5E4M_FromInt(energy): #Take 5E4M format and unpack it into intiger
    assert(energy<0x800000000);#make sure input is an 35 bit number

    if(energy<16): #here the max number is 16 because mantissa has 4 bits, 2^4=16
        return int(energy)
    e = 1
    while(energy>=32):
        e+=1
        energy>>=1
    #print(e,energy)
    return int(16*(e-1)+energy) #format it in as 9 bits = eeeeemmmm, where first 5 are exponent and last 4 are (mantissa - 8)

def unpack5E4M_ToInt(num): #Take intiger as input and pack it into 5E4M format
    assert(num<0x200);#make sure input is an 9 bit number

    e = ((num>>4)&0x1f);#Read first 5 bits from the input number to read the exponent
    m = ((num   )&0x0f);#Read the last 4 bits as mantissa
    #print(e,m)

    if(e==0):
        return m
    elif(e==1):
        return 16+m
    else:
        return (32+2*m+1)<<(e-2)#Recover the fact that this is (mantissa - 8), take into account first multiplication with 2 inside the bracket and then shift to right e-2 time which is equivalent to multiplying by 2


def packInt_FromFloat(energy, constant=10**-8):
    return int(0.5+energy/constant)

def unpackFloat_FromInt(energy, constant=10**-8):
    unpacked_energy = float((energy-0.5)*constant)
    if  unpacked_energy > 0.:
        return unpacked_energy
    else:
        return 0.

def undo_trimming(inputData, targetNumberBits, maxNumberBits):
    criticalBitNumber = maxNumberBits - targetNumberBits
    return inputData << criticalBitNumber

###############################################################
### Functions for converint (u,v) coordinates from mappings used in mapping files vs in CMSSW simulation
###############################################################

def Sector0(layer,u,v): # A function that checks if a given
    if (layer <34) and (layer != 30) and (layer != 32) and (layer != 28):
        if (v-u > 0) and (v >= 0):
            return(True)
    if (layer >= 34) and (layer%2 == 0):
        if (v-u > 0) and (v > 0):
            return(True)
    if (layer >= 34) and (layer%2 == 1):
        if (v-u >= 0) and (v >= 0):
            return(True)
    if (layer == 28) or (layer == 30) or (layer == 32):
        if (u - 2*v <0) and (u+v >= 0):
            return(True)
    return False

def getuvsector(layer,u,v):
    if u == -999:
        return (u,v,0)
    if Sector0(layer,u,v):
        if (layer != 28) and (layer != 30) and (layer != 32):
            return(v-u,v,0)
        else :
            if u >= 0:
                return (v,u,0)
            else :
                return(-u,v-u,0)
    else:
        if  (layer <34):
            u,v = -v,u-v
        if (layer >= 34) and (layer%2 == 0):
            u,v = -v+1,u-v+1
        if (layer >= 34) and (layer%2 == 1):
            u,v = -v-1,u-v-1
        if Sector0(layer,u,v):
            if (layer != 28) and (layer != 30) and (layer != 32):
                return(v-u,v,1)
            else:
                if u >= 0:
                    return (v,u,1)
                else :
                    return(-u,v-u,1)

        else :
            if  (layer <34):
                u,v = -v,u-v
            if (layer >= 34) and (layer%2 == 0):
                u,v = -v+1,u-v+1
            if (layer >= 34) and (layer%2 == 1):
                u,v = -v-1,u-v-1
            if Sector0(layer,u,v):
                if (layer != 28) and (layer != 30) and (layer != 32):
                    return(v-u,v,2)
                else :
                    if u >= 0:
                        return (v,u,2)
                    else :
                        return(-u,v-u,2)

def getuvSTCidxsector(layer,u,v,cellu,cellv):
    if u == -999:
        return (u,v,0,0)
    if Sector0(layer,u,v):
        if (layer != 28) and (layer != 30) and (layer != 32):
            return(v-u,v,0,0)
        else:
            if u >= 0:
                return (v,u,0,1)
            else:
                return(-u,v-u,0,1)
    else:
        if  (layer <34):
            u,v = -v,u-v
        if (layer >= 34) and (layer%2 == 0):
            u,v = -v+1,u-v+1
        if (layer >= 34) and (layer%2 == 1):
            u,v = -v-1,u-v-1
        if Sector0(layer,u,v):
            if (layer != 28) and (layer != 30) and (layer != 32):
                return(v-u,v,0,1)
            else:
                if u >= 0:
                    return (v,u,0,1)
                else:
                    return(-u,v-u,0,1)

        else:
            if  (layer <34):
                u,v = -v,u-v
            if (layer >= 34) and (layer%2 == 0):
                u,v = -v+1,u-v+1
            if (layer >= 34) and (layer%2 == 1):
                u,v = -v-1,u-v-1
            if Sector0(layer,u,v):
                if (layer != 28) and (layer != 30) and (layer != 32):
                    return(v-u,v,0,2)
                else:
                    if u >= 0:
                        return (v,u,0,1)
                    else:
                        return(-u,v-u,0,1)

#######################################################################################
### Functions for converint link index from S1board notation to S2 board notation
#######################################################################################

def s1_link_to_s2_link(s1_board, s1_link): #s1_board is index od S1 board form 0 - 13, s1_link is index of link from 0-5. Links 0 and 5 are connected to S2 boards from different sector and links 1,2,3,4 are connected to boards from the same sector
    s2_link = 99
    if(s1_board < 14):
        s2_link = 14*s1_link + s1_board
    return s2_link

###############################################################
### Functions for list and dictionary manipulations
###############################################################

# A simple function that returns all indices where array had a given value. Useful for example to find indices of a given event_number
def get_index(array, value):
    numpy_array = np.asarray(array).flatten()
    indices = np.where(numpy_array==value)[0]
    return indices

# A simple function that returns all indices for positive or negative endcap's. User specifiels value of encap to define if they want positive or negative side.
def get_endcap_index(array, endcap):
    numpy_array = np.asarray(array)
    if(endcap > 0):
        indices = np.where(numpy_array>0)[0]
    elif(endcap < 0):
        indices = np.where(numpy_array<0)[0]
    return indices

# Function to find the index where gen_eta > 0, there are only two elements in gen_eta for each event
def eta_index(array):
    numpy_array = np.asarray(array)
    if numpy_array[0] > 0:
        return 0
    else:
        return 1
