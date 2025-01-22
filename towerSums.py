#STILL NEEDS COMPREHENSIVE ACCURACY TESTING

import random, re, sys, os, math
import numpy as np
import packingHelper as pkg

# for debuging pruposes
np.set_printoptions(threshold=sys.maxsize)

#****************************
#***************
#FUNCTION DEFINITION PART
#***************
#****************************

def getParametersFromVhFile(inputFileName):
    f = open(inputFileName, 'r')
    lines = f.readlines()

    input_line = lines[1] #taking second line from the top (where input configuration is given in *.vh file)
    output_line = lines[2] #taking thirf line from the top (where output configuration is given in *.vh file)

    in_num = ""

    flag_current_digit = False
    flag_current_alpha = False
    flag_last_digit = False
    flag_last_alpha = False
    flag_start_condition = False
    flag_stop_condition = False
    firstTime = False

    for element in input_line:
        if element.isdigit() == True:
            flag_current_digit = True
            flag_current_alpha = False
            if firstTime == False:
                firstTime = True
        else:
            flag_current_digit = False
            flag_current_alpha = True

        if flag_current_digit == True and flag_last_alpha == True and firstTime == True:
            flag_start_condition = True
        if flag_current_alpha == True and flag_last_digit == True and firstTime == True:
            firstTime = False
            flag_stop_condition = True

        if flag_start_condition == True and flag_stop_condition == False:
            in_num = in_num + element

        flag_last_alpha = flag_current_alpha
        flag_last_digit = flag_current_digit


    out_num = ""

    flag_current_digit = False
    flag_current_alpha = False
    flag_last_digit = False
    flag_last_alpha = False

    flag_start_condition = False
    flag_stop_condition = False

    firstTime = False

    for element in output_line:
        if element.isdigit() == True:
            flag_current_digit = True
            flag_current_alpha = False
            if firstTime == False:
                firstTime = True
        else:
            flag_current_digit = False
            flag_current_alpha = True

        if flag_current_digit == True and flag_last_alpha == True and firstTime == True:
            flag_start_condition = True
        if flag_current_alpha == True and flag_last_digit == True and firstTime == True:
            firstTime = False
            flag_stop_condition = True

        if flag_start_condition == True and flag_stop_condition == False:
            out_num = out_num + element

        flag_last_alpha = flag_current_alpha
        flag_last_digit = flag_current_digit

    return int(in_num), int(out_num)

def vhArchInputToArrayCE_E(inputFileName, output_size, input_size):
    output = np.zeros((output_size, input_size))
    f = open(inputFileName, 'r')
    lines = f.readlines()
    counter = -1
    counter_preamble = 5 #since architecture starts at sixth row from the top (zero indexed)
    for item in lines:
        counter = counter + 1
        if (counter > counter_preamble):
            start_index = item.find('*/') + 3 #3 is due to present tab space to get to mapping itselfe
            tempString = item[start_index:]
            tempString_variable = tempString.strip().split(",")
            tempString_variable = list(filter(None, tempString_variable))
            tempFlag = True
            if len(tempString_variable)>1:
                counter1 = 1
                for i in range(0,int(tempString_variable[0])):
                    output[counter-counter_preamble-1,int(tempString_variable[counter1])] = int(tempString_variable[counter1+1])
                    counter1 = counter1 + 2
    return output

def vhArchInputToArrayCE_H(inputFileName, output_size, input_size, STC):
    if STC == 'STC4':
        number_of_subchannels = 12
    elif STC == 'STC16':
        number_of_subchannels = 3
    elif STC == 'oneSize':
        number_of_subchannels = 6
    else:
        print("Unknown STC architecture!! Please use STC4 or STC16 parameters.")
        exit()
    output = np.zeros((output_size, input_size, number_of_subchannels)) #need two elements in third dimension to store sub-channel number and associated 16th fraction needed
    f = open(inputFileName, 'r')
    lines = f.readlines()
    counter = -1
    counter_preamble = 5 #since architecture starts at sixth row from the top (zero indexed)
    for item in lines:
        counter = counter + 1
        if (counter > counter_preamble):
            start_index = item.find('*/') + 3 #3 is due to present tab space to get to mapping itselfe
            tempString = item[start_index:]
            tempString_variable = tempString.strip().split(",")
            tempString_variable = list(filter(None, tempString_variable))
            tempFlag = True
            if len(tempString_variable)>1: #NE MOGU ISTU LOGIKU PRIMJENITI JER MI SE U ISTOJ LINIJI JEDAN ULANI KANAL MOZE JAVITI VISE PUTA PA CU GA PREBRISAVAT ILI NESTO I REYULTAT NECE BITI DOBAR - ARHITEKTURA PO SVAKOM PODKANALU?
                counter1 = 1
                for i in range(0,int(tempString_variable[0])):
                    output[counter-counter_preamble-1,int(tempString_variable[counter1]),int(tempString_variable[counter1+1])] = int(tempString_variable[counter1+2])
                    counter1 = counter1 + 3

    return output

def readInputEnergies(inputFileName):
    output = []
    f = open(inputFileName, 'r')
    lines = f.readlines()
    for i in range(len(lines)):
        output.append(int(lines[i],2))

    return output

def readInputEnergiesH(inputFileName, input_size): #need new function for reading H energies due to different input format than in case of E (i.e. multiple numbers per row, as opposed to one number per row)
    output = np.zeros((6, input_size))
    counter = -1
    f = open(inputFileName, 'r')
    lines = f.readlines()
    for item in lines:
        counter = counter + 1
        tempString_variable = item.strip().split()
        for i in range(len(tempString_variable)):
            output[i,counter] = int(tempString_variable[i],2)

    return output.astype(np.int64)

def unpackInteger3M(inputData):
    output = []
    for i in range(len(inputData)):
        output.append (pkg.unpack5E3M_ToInt(inputData[i]))

    return output

def unpackInteger4M(inputData, input_size):
    output = np.zeros((6, input_size))
    for i in range(inputData.shape[0]):
        for j in range(inputData.shape[1]):
            output[i,j]=pkg.unpack5E4M_ToInt(inputData[i,j])

    return output


def summation(inputData, matrixArc, summatorVersion, summationTypeFlag): #have removed outputLength as a parameter fro emulator as Python has fixed integer length and we are using only bitwise operators; summationTypeFlag (only for version1) indicates if discarded bits during shifting should be taken into account if their MSB is 1 ()
    output = []
    outputControlNo = 467 #here for debuging purposes! Can be removed along with if-else if statments below with print subcommands (max = 480 i.e. 0 to 479)
    for i in range(len(matrixArc)):
        if summatorVersion == 1:
            sumTemp = 0
            currentArc = matrixArc[i,:] #geting one line representing architecture for one output
            for j in range(len(currentArc)): #goes through all input positions in matrix (currently 102 for Board 3 CE-E)
                if currentArc[j] == 0: #the i-th output is not connected to i-th input, thus pass through
                    pass

                elif currentArc[j] == 1:
                    temp1 = (inputData[j])>>4
                    if ((inputData[j]>>3) & 1)&(summationTypeFlag): #checking if the MSB of discarded part due to shifting right is 1 - if so I increase the summ by 1
                        temp1 = temp1 + 1
                    sumTemp = sumTemp + temp1

                elif currentArc[j] == 2:
                    temp2 = (inputData[j])>>3
                    if ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp2 = temp2 + 1
                    sumTemp = sumTemp + temp2

                elif currentArc[j] == 3:
                    temp3_1 = (inputData[j])>>3
                    temp3_2 = (inputData[j])>>4
                    if ((inputData[j]>>2) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp3_1 = temp3_1 + 1
                        temp3_2 = temp3_2 + 1
                    elif ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp3_1 = temp3_1 + 1
                    elif ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp3_2 = temp3_2 + 1
                    sumTemp = sumTemp +  temp3_1 + temp3_2

                elif currentArc[j] == 4:
                    temp4 = (inputData[j])>>2
                    if ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp4 = temp4 + 1
                    sumTemp = sumTemp + temp4

                elif currentArc[j] == 5:
                    temp5_1 = (inputData[j])>>2
                    temp5_2 = (inputData[j])>>4
                    if ((inputData[j]>>1) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp5_1 = temp5_1 + 1
                        temp5_2 = temp5_2 + 1
                    elif ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp5_1 = temp5_1 + 1
                    elif ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp5_2 = temp5_2 + 1
                    sumTemp = sumTemp + temp5_1 + temp5_2

                elif currentArc[j] == 6:
                    temp6_1 = (inputData[j])>>2
                    temp6_2 = (inputData[j])>>3
                    if ((inputData[j]>>1) & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp6_1 = temp6_1 + 1
                        temp6_2 = temp6_2 + 1
                    elif ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp6_1 = temp6_1 + 1
                    elif ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp6_2 = temp6_2 + 1
                    sumTemp = sumTemp + temp6_1 + temp6_2

                elif currentArc[j] == 7:
                    temp7_1 = (inputData[j])>>2
                    temp7_2 = (inputData[j])>>3
                    temp7_3 = (inputData[j])>>4
                    if ((inputData[j]>>1) & 1) & ((inputData[j]>>2) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp7_1 = temp7_1 + 1
                        temp7_2 = temp7_2 + 1
                        temp7_3 = temp7_3 + 1
                    elif ((inputData[j]>>1) & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp7_1 = temp7_1 + 1
                        temp7_2 = temp7_2 + 1
                    elif ((inputData[j]>>1) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp7_1 = temp7_1 + 1
                        temp7_3 = temp7_3 + 1
                    elif ((inputData[j]>>2) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp7_2 = temp7_2 + 1
                        temp7_3 = temp7_3 + 1
                    elif ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp7_1 = temp7_1 + 1
                    elif ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp7_2 = temp7_2 + 1
                    elif ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp7_3 = temp7_3 + 1
                    sumTemp = sumTemp + temp7_1 + temp7_2 + temp7_3

                elif currentArc[j] == 8:
                    temp8 = (inputData[j])>>1
                    if (inputData[j] & 1)&(summationTypeFlag):
                        temp8 = temp8 + 1
                    sumTemp = sumTemp + temp8

                elif currentArc[j] == 9:
                    temp9_1 = (inputData[j])>>1
                    temp9_2 = (inputData[j])>>4
                    if (inputData[j] & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp9_1 = temp9_1 + 1
                        temp9_2 = temp9_2 + 1
                    elif (inputData[j] & 1)&(summationTypeFlag):
                        temp9_1 = temp9_1 + 1
                    elif ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp9_2 = temp9_2 + 1
                    sumTemp = sumTemp + temp9_1 + temp9_2

                elif currentArc[j] == 10:
                    temp10_1 = (inputData[j])>>1
                    temp10_2 = (inputData[j])>>3
                    if (inputData[j] & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp10_1 = temp10_1 + 1
                        temp10_2 = temp10_2 + 1
                    elif (inputData[j] & 1)&(summationTypeFlag):
                        temp10_1 = temp10_1 + 1
                    elif ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp10_2 = temp10_2 + 1
                    sumTemp = sumTemp + temp10_1 + temp10_2

                elif currentArc[j] == 11:
                    temp11_1 = (inputData[j])>>1
                    temp11_2 = (inputData[j])>>3
                    temp11_3 = (inputData[j])>>4
                    if (inputData[j] & 1) & ((inputData[j]>>2) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp11_1 = temp11_1 + 1
                        temp11_2 = temp11_2 + 1
                        temp11_3 = temp11_3 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp11_1 = temp11_1 + 1
                        temp11_2 = temp11_2 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp11_1 = temp11_1 + 1
                        temp11_3 = temp11_3 + 1
                    elif ((inputData[j]>>2) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp11_2 = temp11_2 + 1
                        temp11_3 = temp11_3 + 1
                    elif (inputData[j] & 1)&(summationTypeFlag):
                        temp11_1 = temp11_1 + 1
                    elif ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp11_2 = temp11_2 + 1
                    elif ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp11_3 = temp11_3 + 1
                    sumTemp = sumTemp + temp11_1 + temp11_2 + temp11_3

                elif currentArc[j] == 12:
                    temp12_1 = (inputData[j])>>1
                    temp12_2 = (inputData[j])>>2
                    if (inputData[j] & 1) & ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp12_1 = temp12_1 + 1
                        temp12_2 = temp12_2 + 1
                    elif (inputData[j] & 1)&(summationTypeFlag):
                        temp12_1 = temp12_1 + 1
                    elif ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp12_2 = temp12_2 + 1
                    sumTemp = sumTemp + temp12_1 + temp12_2

                elif currentArc[j] == 13:
                    temp13_1 = (inputData[j])>>1
                    temp13_2 = (inputData[j])>>2
                    temp13_3 = (inputData[j])>>4
                    if (inputData[j] & 1) & ((inputData[j]>>1) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp13_1 = temp13_1 + 1
                        temp13_2 = temp13_2 + 1
                        temp13_3 = temp13_3 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp13_1 = temp13_1 + 1
                        temp13_2 = temp13_2 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp13_1 = temp13_1 + 1
                        temp13_3 = temp13_3 + 1
                    elif ((inputData[j]>>1) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp13_2 = temp13_2 + 1
                        temp13_3 = temp13_3 + 1
                    elif (inputData[j] & 1)&(summationTypeFlag):
                        temp13_1 = temp13_1 + 1
                    elif ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp13_2 = temp13_2 + 1
                    elif ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp13_3 = temp13_3 + 1
                    sumTemp = sumTemp + temp13_1 + temp13_2 + temp13_3

                elif currentArc[j] == 14:
                    temp14_1 = (inputData[j])>>1
                    temp14_2 = (inputData[j])>>2
                    temp14_3 = (inputData[j])>>3
                    if (inputData[j] & 1) & ((inputData[j]>>1) & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp14_1 = temp14_1 + 1
                        temp14_2 = temp14_2 + 1
                        temp14_3 = temp14_3 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp14_1 = temp14_1 + 1
                        temp14_2 = temp14_2 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp14_1 = temp14_1 + 1
                        temp14_3 = temp14_3 + 1
                    elif ((inputData[j]>>1) & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp14_2 = temp14_2 + 1
                        temp14_3 = temp14_3 + 1
                    elif (inputData[j] & 1)&(summationTypeFlag):
                        temp14_1 = temp14_1 + 1
                    elif ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp14_2 = temp14_2 + 1
                    elif ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp14_3 = temp14_3 + 1
                    sumTemp = sumTemp + temp14_1 + temp14_2 + temp14_3

                elif currentArc[j] == 15:
                    temp15_1 = (inputData[j])>>1
                    temp15_2 = (inputData[j])>>2
                    temp15_3 = (inputData[j])>>3
                    temp15_4 = (inputData[j])>>4
                    if (inputData[j] & 1) & ((inputData[j]>>1) & 1) & ((inputData[j]>>2) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp15_1 = temp15_1 + 1
                        temp15_2 = temp15_2 + 1
                        temp15_3 = temp15_3 + 1
                        temp15_4 = temp15_4 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>1) & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp15_1 = temp15_1 + 1
                        temp15_2 = temp15_2 + 1
                        temp15_3 = temp15_3 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>1) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp15_1 = temp15_1 + 1
                        temp15_2 = temp15_2 + 1
                        temp15_4 = temp15_4 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>2) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp15_1 = temp15_1 + 1
                        temp15_3 = temp15_3 + 1
                        temp15_4 = temp15_4 + 1
                    elif ((inputData[j]>>1) & 1) & ((inputData[j]>>2) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp15_2 = temp15_2 + 1
                        temp15_3 = temp15_3 + 1
                        temp15_4 = temp15_4 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp15_1 = temp15_1 + 1
                        temp15_2 = temp15_2 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp15_1 = temp15_1 + 1
                        temp15_3 = temp15_3 + 1
                    elif (inputData[j] & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp15_1 = temp15_1 + 1
                        temp15_4 = temp15_4 + 1
                    elif ((inputData[j]>>1) & 1) & ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp15_2 = temp15_2 + 1
                        temp15_3 = temp15_3 + 1
                    elif ((inputData[j]>>1) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp15_2 = temp15_2 + 1
                        temp15_4 = temp15_4 + 1
                    elif ((inputData[j]>>2) & 1) & ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp15_3 = temp15_3 + 1
                        temp15_4 = temp15_4 + 1
                    elif (inputData[j] & 1):
                        temp15_1 = temp15_1 + 1
                    elif ((inputData[j]>>1) & 1)&(summationTypeFlag):
                        temp15_2 = temp15_2 + 1
                    elif ((inputData[j]>>2) & 1)&(summationTypeFlag):
                        temp15_3 = temp15_3 + 1
                    elif ((inputData[j]>>3) & 1)&(summationTypeFlag):
                        temp15_4 = temp15_4 + 1
                    sumTemp = sumTemp + temp15_1 + temp15_2 + temp15_3 + temp15_4

                elif currentArc[j] == 16:
                    sumTemp = sumTemp + inputData[j]
            output.append(sumTemp)

        elif summatorVersion==2:
            sumTemp = 0
            currentArc = matrixArc[i,:] #geting one line representing architecture for one output
            for j in range(len(currentArc)): #goes through all input positions in matrix (currently 102 for Board 3 CE-E)
                if currentArc[j] == 0: #the i-th output is not connected to i-th input, thus pass through
                    pass

                elif currentArc[j] == 1:
                    sumTemp = sumTemp + inputData[j]

                elif currentArc[j] == 2:
                    sumTemp = sumTemp + 2*inputData[j]

                elif currentArc[j] == 3:
                    sumTemp = sumTemp +  3*inputData[j]

                elif currentArc[j] == 4:
                    sumTemp = sumTemp + 4*inputData[j]

                elif currentArc[j] == 5:
                    sumTemp = sumTemp + 5*inputData[j]

                elif currentArc[j] == 6:
                    sumTemp = sumTemp + 6*inputData[j]

                elif currentArc[j] == 7:
                    sumTemp = sumTemp + 7*inputData[j]

                elif currentArc[j] == 8:
                    sumTemp = sumTemp + 8*inputData[j]

                elif currentArc[j] == 9:
                    sumTemp = sumTemp + 9*inputData[j]

                elif currentArc[j] == 10:
                    sumTemp = sumTemp + 10*inputData[j]

                elif currentArc[j] == 11:
                    sumTemp = sumTemp + 11*inputData[j]

                elif currentArc[j] == 12:
                    sumTemp = sumTemp + 12*inputData[j]

                elif currentArc[j] == 13:
                    sumTemp = sumTemp + 13*inputData[j]

                elif currentArc[j] == 14:
                    sumTemp = sumTemp + 14*inputData[j]

                elif currentArc[j] == 15:
                    sumTemp = sumTemp + 15*inputData[j]

                elif currentArc[j] == 16:
                    sumTemp = sumTemp + 16*inputData[j]
            output.append(sumTemp>>4)

    return output

def overflowChecker(inputData,overflowBit):
    output = []
    for i in range(len(inputData)):
        if (inputData[i]>>(overflowBit)):
            #overflow accured
            templateString = '1'
            templateNumberStr = templateString*overflowBit
            output.append(int(templateNumberStr, 2)) #equivalent to saturated value at overflowBit number of bits
            #for debug purposes
            print("!!Overflow occured!! Saturating output to max value! Check results!")
            print(i)

        else:
            output.append(inputData[i])
    return output

def trimming(inputData, targetNumberBits, MSB):
    assert(MSB>=targetNumberBits) #because it does not make any sens to take less bits than there is space in packed word (currently, 19 bits)
    output = []
    #constructing selection mask so to set all bits left of MSB to zero
    maskString = '1'*MSB
    maskInt = int(maskString,2)
    criticalBitNumber = MSB - targetNumberBits
    for i in range(len(inputData)):
        output.append((inputData[i]&maskInt)>>criticalBitNumber)

    return output

def packInteger(inputData):
    output = []
    for i in range(len(inputData)):
        output.append (pkg.pack5E3M_FromInt(inputData[i]))

    return output

def packInteger4E4M(inputData):
    output = []
    for i in range(len(inputData)):
        output.append (pkg.pack4E4M_FromInt(inputData[i]))

    return output


#****************************
#***************
#THE MAIN PART OF TOWER SUMM MODULE
#***************
#****************************

#for debuging (writing intermediate results to console)
debugMode = False

#Going over all 3 sectors
for s in range(3):
    #Going over all of 14 boards
    for i in range(14): #14:
        #defining names of file from which to read mapping and architecture. Currently we chose board #3 so it will be used here.
        fileName_CE_E_Architecture = '../Firmware/inputs/v2/CE_E_' + str(i) + '_v2.vh'
        fileName_CE_H_Architecture = '../Firmware/inputs/v2/CE_H_' + str(i) + '_v2.vh'

        fileName_CE_E_Inputs = '../Emulator/output/Stage1_Unpacker/CEE/Sector_' + str(s) + '_Board_' + str(i) + '.txt'
        fileName_CE_H_Inputs = '../Emulator/output/Stage1_Unpacker/CEH/Sector_' + str(s) + '_Board_' + str(i) + '.txt'

        STC_architecture = 'oneSize' #or STC4, STC16 or oneSize

        if (os.path.isfile(fileName_CE_E_Architecture)):
            #reading the actual *.vh file content. This step is sensitive to *ANY* change in *.vh file formatting and should be adjusted if needed (since string parsing is used in getParameters function)
            #first, number of input and output lines is fetched
            in_E_num, out_E_num = getParametersFromVhFile(fileName_CE_E_Architecture)

            #secondly, input to output mapping is fetched
            matVariable_CE_E = vhArchInputToArrayCE_E(fileName_CE_E_Architecture, out_E_num, in_E_num)
        else:
            matVariable_CE_E = []
            in_E_num = 0
            out_E_num = 0
            print("Sector " + str(s) + "Board " + str(i) + " CE_E architecture not detected! Generating an empty array!")

        if (os.path.isfile(fileName_CE_H_Architecture)):
            #reading the actual *.vh file content. This step is sensitive to *ANY* change in *.vh file formatting and should be adjusted if needed (since string parsing is used in getParameters function)
            #first, number of input and output lines is fetched
            in_H_num, out_H_num = getParametersFromVhFile(fileName_CE_H_Architecture)

            #secondly, input to output mapping is fetched
            matVariable_CE_H = vhArchInputToArrayCE_H(fileName_CE_H_Architecture, out_H_num, in_H_num, STC_architecture)
        else:
            matVariable_CE_H = []
            in_H_num = 0
            out_H_num = 0
            print("Sector " + str(s) + "Board " + str(i) + " CE_H architecture not detected! Generating an empty array!")


        if (os.path.isfile(fileName_CE_E_Inputs)):
            #Generating inputs in decimal format (up to value of 255)
            #Assumption: inputs are in 5E3M format
            inputArray_CE_E = readInputEnergies(fileName_CE_E_Inputs)

            #integer unpacking
            decodedInputArray_CE_E = unpackInteger3M(inputArray_CE_E)

            # Doing the summation (on upacked data, integers)
            summedValues_CE_E = summation(decodedInputArray_CE_E, matVariable_CE_E, 2, False) #parameter 1 or 2 indicates the mode of summation (for study purposes different summation techniques have been implemented), if version 2 is selected the subsequent False parameter is disregarded (i.e. it is a valid parameter only for version 1 of the sumator)

            #Checking for summation overflow (which can not be correctly coded with 5E3M format)
            checkedOutputValues_CE_E = overflowChecker(summedValues_CE_E,34) #second parameter is maximum number of allowed bits, 34 bits in case of 5E3M

            trimmedOutputValues_CE_E = trimming(checkedOutputValues_CE_E, 19, 34) #trimming to 19 bit (4E4M) - taking first 19 MSBs  (requied parameters> targetNumberBits, maxNzmberBits)

            # converting the summs from pure integer number format to 4E4M format
            outputValues_CE_E = packInteger4E4M(trimmedOutputValues_CE_E)
        else:
            #implementing all zeros since there is no connection to cuurent board
            outputValues_CE_E = np.zeros(out_E_num, dtype=int)
            print("Sector " + str(s) + " Board " + str(i) + " E inputs not detected! Filling output with zeros!")


        if (os.path.isfile(fileName_CE_H_Inputs)):
            #Generating inputs in decimal format (up to value of 255)
            #Assumption: inputs are in 5E4M format
            inputArray_CE_H = readInputEnergiesH(fileName_CE_H_Inputs, in_H_num)

            #integer unpacking
            decodedInputArray_CE_H = unpackInteger4M(inputArray_CE_H, in_H_num)

            # Doing the summation (on upacked data, integers) - since there are 6 channels (0-5) summation will be done in for loop
            summedValues_CE_H = []
            for k in range(6):#6
                if k == 0:
                    temp1_sum = summation(decodedInputArray_CE_H[k,:].astype(np.int64), matVariable_CE_H[:,:,k].astype(np.int64), 2, False) #parameter 1 or 2 indicates the mode of summation (for study purposes different summation techniques have been implemented), if version 2 is selected the subsequent False parameter is disregarded (i.e. it is a valid parameter only for version 1 of the sumator)
                    summedValues_CE_H = np.copy(temp1_sum)
                else:
                    temp1_sum = summation(decodedInputArray_CE_H[k,:].astype(np.int64), matVariable_CE_H[:,:,k].astype(np.int64), 2, False)
                    summedValues_CE_H = [sum(x) for x in zip(summedValues_CE_H, np.copy(temp1_sum))]

            #Checking for summation overflow (which can not be correctly coded with 5E3M format)
            checkedOutputValues_CE_H = overflowChecker(summedValues_CE_H,35) #35 because summation is in 5E4M format

            trimmedOutputValues_CE_H = trimming(checkedOutputValues_CE_H, 19, 35) #trimming to 19 bit (4E4M) - taking first 19 MSBs  (requied parameters> targetNumberBits, maxNzmberBits)

            #converting the summs from pure integer number format to 5E3M format
            outputValues_CE_H = packInteger4E4M(trimmedOutputValues_CE_H)
        else:
            #implementing all zeros since there is no connection to cuurent board
            outputValues_CE_H = np.zeros(out_H_num, dtype=int)
            print("Sector " + str(s) + " Board " + str(i) + " H inputs not detected! Filling output with zeros!")


        # for debuging pruposes (set debugMode flag to True)
        if debugMode:
            #print("Architecture:")
            #print(matVariable_CE_E)
            print("Sector No:")
            print(s)
            print("Board No:")
            print(i)

            print("Input energies CE_E (RAW): ")
            print(inputArray_CE_E)
            print("Input energies CE_E (DECODED): ")
            print(decodedInputArray_CE_E)
            print("Summed values CE_E (RAW): ")
            print(summedValues_CE_E)
            print("Summed and saturated values CE_E (S-RAW): ")
            print(checkedOutputValues_CE_E)
            print("Summed and trimmed values CE_E (S-RAW): ")
            print(trimmedOutputValues_CE_E)
            print("Summed values CE_E (CODED): ")
            print(outputValues_CE_E)

            print("Input energies CE_H (RAW): ")
            print(inputArray_CE_H)
            print("Input energies CE_H (DECODED): ")
            print(decodedInputArray_CE_H)
            print("Summed values CE_H (RAW): ")
            print(summedValues_CE_H)
            print("Summed and saturated values CE_H (S-RAW): ")
            print(checkedOutputValues_CE_H)
            print("Summed and trimmed values CE_H (S-RAW): ")
            print(trimmedOutputValues_CE_H)
            print("Summed values CE_H (CODED): ")
            print(outputValues_CE_H)


    # #***********Writing files - CE_E channel*********************
        with open(os.path.join('../Emulator/output/Stage1_TowerSums/', 'TowerSums_Sector_' + str(s) + '_Board_' + str(i) + '_CE_E' + '.txt'), 'w') as f:
            for k in range (len(outputValues_CE_E)):
                if k == len(outputValues_CE_E)-1:
                    f.write(f"{outputValues_CE_E[k]:02x}")
                else:
                    f.write(f"{outputValues_CE_E[k]:02x}\n")


    # #***********Writing files - CE_H channel_Trimmed*********************
        with open(os.path.join('../Emulator/output/Stage1_TowerSums/', 'TowerSums_Sector_' + str(s) + '_Board_' + str(i) + '_CE_H' + '.txt'), 'w') as f:
             for n in range (len(outputValues_CE_H)):
                if n == len(outputValues_CE_H)-1:
                    f.write(f"{outputValues_CE_H[n]:02x}")
                else:
                    f.write(f"{outputValues_CE_H[n]:02x}\n")
