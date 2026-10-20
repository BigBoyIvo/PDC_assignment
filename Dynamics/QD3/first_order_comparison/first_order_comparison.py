import tclab
import numpy as np
import time
import matplotlib.pyplot as plt

# Default FOPDT model
Kp_def = 0.5      # degC/%
tauP_def = 120.0  # seconds
thetaP_def = 10   # seconds (integer)

#######################################################
# FOPDT model - PUT YOUR MODEL HERE
Kp_emp = 0.664    # degC/%
tauP_emp = 159.0  # seconds
thetaP_emp = 6    # seconds (integer)
#######################################################

Tss = 23      # degC (ambient temperature)
Qss = 0       # % heater

# save txt file with data and set point
# t = time
# u1,u2 = heaters
# y1,y2 = tempeatures
# sp1,sp2 = setpoints
def save_txt(t, u1, u2, y1, y2):
    data = np.vstack((t, u1, u2, y1, y2))  # vertical stack
    data = data.T  # transpose data
    top = ('Time (sec), Heater 1 (%), Heater 2 (%), ' 
           'Temperature 1 (degC), Temperature 2 (degC), '
           )
    np.savetxt('data_FOModels.txt', data, delimiter=',', header=top, comments='')

# Connect to Arduino
a = tclab.TCLab()

# Turn LED on
print('LED On')
a.LED(100)

# Run time in minutes
run_time = 10.0

# Number of cycles
loops = int(60.0*run_time)
tm = np.zeros(loops)

# Temperature (K)
Tsp1 = np.ones(loops) * 23.0 # set point (degC)
T1 = np.ones(loops) * a.T1 # measured T (degC)

Tsp2 = np.ones(loops) * 23.0 # set point (degC)
T2 = np.ones(loops) * a.T2 # measured T (degC)

# Predictions (Default)
Tpl_def = np.ones(loops) * a.T1
error_fopdt_def = np.zeros(loops)

# Predictions (Empirical)
Tpl_emp = np.ones(loops) * a.T1
error_fopdt_emp = np.zeros(loops)

# impulse tests (0 - 100%)
Q1 = np.ones(loops) * 0.0
Q2 = np.ones(loops) * 0.0
Q1[10:110] = 50.0 # step up for 100 sec
Q1[200:300] = 90.0 # step up for 100 sec
Q1[400:500] = 70.0 # step up for 100 sec

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
            time.sleep(sleep-0.01)
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

        # Simulate one time step with Default FOPDT model
        z_def = np.exp(-dt/tauP_def)
        Tpl_def[i] = (Tpl_def[i-1]-Tss) * z_def \
                 + (Q1[max(0,i-int(thetaP_def)-1)]-Qss)*(1-z_def)*Kp_def \
                 + Tss
        error_fopdt_def[i] = error_fopdt_def[i-1] + abs(Tpl_def[i]-T1[i])

        # Simulate one time step with Empirical FOPDT model
        z_emp = np.exp(-dt/tauP_emp)
        Tpl_emp[i] = (Tpl_emp[i-1]-Tss) * z_emp \
                 + (Q1[max(0,i-int(thetaP_emp)-1)]-Qss)*(1-z_emp)*Kp_emp \
                 + Tss
        error_fopdt_emp[i] = error_fopdt_emp[i-1] + abs(Tpl_emp[i]-T1[i])

        # Write output (0-100)
        a.Q1(Q1[i])
        a.Q2(Q2[i])

        # Print line of data
        print('{:6.1f} {:6.2f} {:6.2f} {:6.2f} {:6.2f}'.format(tm[i], \
                                                               Q1[i], \
                                                               Q2[i], \
                                                               T1[i], \
                                                               T2[i]))

        # Plot
        plt.clf()
        ax=plt.subplot(3,1,1)
        ax.grid()
        plt.plot(tm[0:i],T1[0:i],'ro',label=r'$T_1$ measured')
        plt.plot(tm[0:i],Tpl_def[0:i],'m--',label=r'$T_1$ Default FOPDT')
        plt.plot(tm[0:i],Tpl_emp[0:i],'g:',label=r'$T_1$ Empirical FOPDT')
        plt.plot(tm[0:i],T2[0:i],'bx',label=r'$T_2$ measured')
        plt.ylabel('Temperature (degC)')
        plt.legend(loc=2)
        
        ax=plt.subplot(3,1,2)
        ax.grid()
        plt.plot(tm[0:i],error_fopdt_def[0:i],'m--',label='Default Error')
        plt.plot(tm[0:i],error_fopdt_emp[0:i],'g:',label='Empirical Error')
        plt.ylabel('Cumulative Error')
        plt.legend(loc='best')
        
        ax=plt.subplot(3,1,3)
        ax.grid()
        plt.plot(tm[0:i],Q1[0:i],'r-',label=r'$Q_1$')
        plt.plot(tm[0:i],Q2[0:i],'b:',label=r'$Q_2$')
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
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i])
    # Save figure
    plt.savefig('test_FOModels.png')
    
# Allow user to end loop with Ctrl-C           
except KeyboardInterrupt:
    # Disconnect from Arduino
    a.Q1(0)
    a.Q2(0)
    print('Shutting down')
    a.close()
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i])
    plt.savefig('test_FOModels.png')
    
# Make sure serial connection still closes when there's an error
except:           
    # Disconnect from Arduino
    a.Q1(0)
    a.Q2(0)
    print('Error: Shutting down')
    a.close()
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i])
    plt.savefig('test_FOModels.png')
    raise