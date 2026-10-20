import tclab
import numpy as np
import time
import matplotlib.pyplot as plt

###########################################################################
# This file does not need modifications
# Running time - approximately 40 minutes
###########################################################################


# Connect to Arduino
a = tclab.TCLab()

# save txt file with data and set point
# t = time
# u1,u2 = heaters
# y1,y2 = tempeatures
# sp1,sp2 = additional measurements
def save_txt(t, u1, u2, y1, y2, sp1, sp2):
    data = np.vstack((t, u1, u2, y1, y2, sp1, sp2))  # vertical stack
    data = data.T  # transpose data
    top = ('Time (sec), Heater 1 (%), Heater 2 (%), ' 
           'Temperature 1 (degC), Temperature 2 (degC), '
           'Input 1 (%), Input 2 (%)')
    np.savetxt('data_DataCollection.txt', data, delimiter=',', header=top, comments='')   #####DO NOT CHANGE THE FILENAME

# Get Version
print(a.version)

# Turn LED on
print('LED On')
a.LED(100)

# Run time in minutes
run_time = 40.0

# Number of cycles
loops = int(60.0*run_time)
tm = np.zeros(loops)

# Temperature (K)
T1 = np.ones(loops) * a.T1 # measured T (degC)

T2 = np.ones(loops) * a.T2 # measured T (degC)

# impulse tests
H1 = np.ones(loops) * 0.0
H2 = np.ones(loops) * 0.0

Q1 = np.zeros(loops)
Q2 = np.zeros(loops)

Q1[10:60] = 30
Q1[150:250] = 10
Q1[250:400] = 100
Q1[450:550] = 0
Q1[550:750] = 40
Q1[900:950] = 50
Q1[950:1150] = 80
Q1[1250:1500] = 40


Q2[100:200] = 50
Q2[200:300] = 20
Q2[300:400] = 70
Q2[400:500] = 10
Q2[500:600] = 100
Q2[1800:1900] = 80
Q2[2000:2100] = 35

print('Running Main Loop. Ctrl-C to end.')
print('  Time   Q1     Q2    T1     T2')
print('{:6.1f} {:6.2f} {:6.2f} {:6.2f} {:6.2f}'.format(tm[0], \
                                                       Q1[0], \
                                                       Q2[0], \
                                                       T1[0], \
                                                       T2[0]))

# Create plot
plt.figure(figsize=(10,7))
plt.ion()
plt.show()

# Main Loop
start_time = time.time()
prev_time = start_time
try:
    for i in range(1,loops):
        # Sleep time
        sleep_max = 1.0
        sleep = sleep_max - (time.time() - prev_time)
        if sleep>=0.01:
            time.sleep(sleep)
        else:
            time.sleep(0.01)

        # Record time and change in time
        t = time.time()
        dt = t - prev_time
        prev_time = t
        tm[i] = t - start_time
                    
        # Read temperatures in Kelvin 
        T1[i] = a.T1
        T2[i] = a.T2

        # Write output (0-100)
        a.Q1(Q1[i])
        a.Q2(Q2[i])

        # Print line of data
        print('{:6.2f} {:6.2f} {:6.2f} {:6.2f} {:6.2f}'.format(tm[i], \
                                                               Q1[i], \
                                                               Q2[i], \
                                                               T1[i], \
                                                               T2[i]))


        # Plot
        plt.clf()
        ax=plt.subplot(2,1,1)
        ax.grid()
        plt.plot(tm[0:i],T1[0:i],'ro',label=r'$T_1$')
        plt.plot(tm[0:i],T2[0:i],'bx',label=r'$T_2$')
        plt.ylabel('Temperature (degC)')
        plt.legend(loc='best')
        ax=plt.subplot(2,1,2)
        ax.grid()
        plt.plot(tm[0:i],Q1[0:i],'r-',label=r'$Q_1$')
        plt.plot(tm[0:i],Q2[0:i],'b:',label=r'$Q_2$')
        plt.plot(tm[0:i],H1[0:i],'r--',label=r'$H_1$')
        plt.plot(tm[0:i],H2[0:i],'b-.',label=r'$H_2$')

        plt.ylabel('Heaters')
        plt.xlabel('Time (sec)')
        plt.legend(loc='best')
        plt.draw()
        plt.pause(0.05)

    # Turn off heaters
    a.Q1(0)
    a.Q2(0)
    a.close()
    # Save text file
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i],H1[0:i],H2[0:i])
    # Save figure
    plt.savefig('test_DataCollection.png') #####DO NOT CHANGE THE FILENAME
        
# Allow user to end loop with Ctrl-C           
except KeyboardInterrupt:
    # Disconnect from Arduino
    a.Q1(0)
    a.Q2(0)
    print('Shutting down')
    a.close()
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i],H1[0:i],H2[0:i])
    plt.savefig('test_DataCollection.png') #####DO NOT CHANGE THE FILENAME
    
# Make sure serial connection still closes when there's an error
except:           
    # Disconnect from Arduino
    a.Q1(0)
    a.Q2(0)
    print('Error: Shutting down')
    a.close()
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i],H1[0:i],H2[0:i])
    plt.savefig('test_DataCollection.png') #####DO NOT CHANGE THE FILENAME
    raise
