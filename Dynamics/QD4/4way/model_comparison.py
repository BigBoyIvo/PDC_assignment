import tclab  # pip install tclab
import numpy as np
import time
import matplotlib.pyplot as plt
from scipy.integrate import odeint


############################################CHANGE HERE AS NEEDED#################################
# Parameters:
Ta = 23 + 273.15   # K ####Change to your ambient temp

# Default values
U = 10.0           # W/m^2-K
m = 4.0/1000.0     # kg
Cp = 0.5 * 1000.0  # J/kg-K    
A = 10.0 / 100.0**2 # Area in m^2
As = 2.0 / 100.0**2 # Area in m^2
a1 = 0.0100     # W / % heater 1
a2 = 0.0075     # W / % heater 2
eps = 0.9          # Emissivity

alpha_default = [Ta, U*A/m/Cp, eps*A/m/Cp, U*As/m/Cp, eps*As/m/Cp, a1/m/Cp, a2/m/Cp]
######For system identification:

alpha_identified = [Ta, 0.003660, 0, 0.001810, 0, 0.003194, 0.001565]

#####Time settings:
# Run time in minutes
run_time = 10.0
######Number of cycles - DO NOT CHANGE
loops = int(60.0*run_time)
######################################

#######################################################
# FOPDT models - ALL FOUR EMPIRICAL TRANSFER FUNCTIONS
# G_Q1->T1 (Direct)
K11 = 0.664; tau11 = 159.0; theta11 = 6
# G_Q2->T1 (Cross-heating from Q2)
K12 = 0.174; tau12 = 263.0; theta12 = 31

# G_Q1->T2 (Cross-heating from Q1)
K21 = 0.352; tau21 = 147.0; theta21 = 24 
# G_Q2->T2 (Direct)
K22 = 0.144; tau22 = 224.0; theta22 = 56

Tss = 24.0  # degC (ambient temperature)
Qss = 0.0   # % heater
#######################################################

# Impulse tests (0 - 100%)
Q1 = np.ones(loops) * 0.0
Q2 = np.ones(loops) * 0.0
Q1[5:50] = 100.0 # step up
Q1[110:220] = 80.0 # step up for 10 sec
Q1[340:440] = 50.0 # step up for 20 sec

Q2[50:150] = 50
Q2[300:400] = 100.0 # 

###################################################################################################

# define energy balance model
# define energy balance model
def heat(x,t,Q1,Q2,params):
    Ta, alpha1, alpha2, alpha3, alpha4, alpha5, alpha6 = params
    sigma = 5.67e-8    # Stefan-Boltzman

    # Temperature States
    T1 = x[0]
    T2 = x[1]

    # Nonlinear Energy Balances using Alphas
    dT1dt = alpha1*(Ta - T1) + alpha2*sigma*(Ta**4 - T1**4) \
            + alpha3*(T2 - T1) + alpha4*sigma*(T2**4 - T1**4) + alpha5*Q1
            
    dT2dt = alpha1*(Ta - T2) + alpha2*sigma*(Ta**4 - T2**4) \
            - alpha3*(T2 - T1) - alpha4*sigma*(T2**4 - T1**4) + alpha6*Q2

    return [dT1dt, dT2dt]

# save txt file
def save_txt(t,u1,u2,y1,y2):
    data = np.vstack((t,u1,u2,y1,y2))  # vertical stack
    data = data.T                 # transpose data
    top = 'Time (sec), Heater 1 (%), Heater 2 (%), ' \
        + 'Temperature 1 (degC), Temperature 2 (degC), '
    np.savetxt('data_allModels.txt',data,delimiter=',',header=top,comments='')


# Connect to Arduino
a = tclab.TCLab()

# Turn LED on
print('LED On')
a.LED(100)

tm = np.zeros(loops)

# Temperature (K)
T1 = np.ones(loops) * a.T1 # measured T (degC)

T2 = np.ones(loops) * a.T2 # measured T (degC)

# Predictions (Default Energy Balance)
Tp1 = np.ones(loops) * a.T1
Tp2 = np.ones(loops) * a.T2
error_eb = np.zeros(loops)

# Predictions (Identified Energy Balance)
Tp1_id = np.ones(loops) * a.T1
Tp2_id = np.ones(loops) * a.T2
error_eb_id = np.zeros(loops)

# FOPDT Deviation Tracking Arrays
dT11 = np.zeros(loops) # Delta T1 caused by Q1
dT12 = np.zeros(loops) # Delta T1 caused by Q2
dT21 = np.zeros(loops) # Delta T2 caused by Q1
dT22 = np.zeros(loops) # Delta T2 caused by Q2

# Final combined FOPDT predictions
Tpl_emp1 = np.ones(loops) * a.T1
Tpl_emp2 = np.ones(loops) * a.T2
error_fopdt_emp = np.zeros(loops)


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

        # Simulate Default Energy Balance
        Tinit = [Tp1[i-1]+273.15, Tp2[i-1]+273.15]
        Tnext = odeint(heat, Tinit, [0,dt], args=(Q1[i-1], Q2[i-1], alpha_default))
        Tp1[i] = Tnext[1,0]-273.15
        Tp2[i] = Tnext[1,1]-273.15
        error_eb[i] = error_eb[i-1] + (abs(Tp1[i]-T1[i]) + abs(Tp2[i]-T2[i]))*dt

        # Simulate Identified Energy Balance
        Tinit_id = [Tp1_id[i-1]+273.15, Tp2_id[i-1]+273.15]
        Tnext_id = odeint(heat, Tinit_id, [0,dt], args=(Q1[i-1], Q2[i-1], alpha_identified))
        Tp1_id[i] = Tnext_id[1,0]-273.15
        Tp2_id[i] = Tnext_id[1,1]-273.15
        error_eb_id[i] = error_eb_id[i-1] + (abs(Tp1_id[i]-T1[i]) + abs(Tp2_id[i]-T2[i]))*dt

        # Simulate Empirical FOPDT (Superposition of all 4 transfer functions)
        
        # 1. Effect of Q1 on T1
        z11 = np.exp(-dt/tau11)
        dT11[i] = dT11[i-1]*z11 + (Q1[max(0, i-int(theta11)-1)] - Qss)*(1-z11)*K11
        
        # 2. Effect of Q2 on T1
        z12 = np.exp(-dt/tau12)
        dT12[i] = dT12[i-1]*z12 + (Q2[max(0, i-int(theta12)-1)] - Qss)*(1-z12)*K12

        # 3. Effect of Q1 on T2
        z21 = np.exp(-dt/tau21)
        dT21[i] = dT21[i-1]*z21 + (Q1[max(0, i-int(theta21)-1)] - Qss)*(1-z21)*K21

        # 4. Effect of Q2 on T2
        z22 = np.exp(-dt/tau22)
        dT22[i] = dT22[i-1]*z22 + (Q2[max(0, i-int(theta22)-1)] - Qss)*(1-z22)*K22

        # Sum the deviations and add the ambient baseline
        Tpl_emp1[i] = dT11[i] + dT12[i] + Tss
        Tpl_emp2[i] = dT21[i] + dT22[i] + Tss

        # Total absolute error (T1 + T2 combined)
        error_fopdt_emp[i] = error_fopdt_emp[i-1] + abs(Tpl_emp1[i]-T1[i]) + abs(Tpl_emp2[i]-T2[i])

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
        
        # 1. T1 Temperature Graph
        ax=plt.subplot(4,1,1)
        ax.grid()
        plt.plot(tm[0:i],T1[0:i],'ro',label=r'$T_1$ measured')
        plt.plot(tm[0:i],Tp1[0:i],'k-',label=r'$T_1$ default EB')
        plt.plot(tm[0:i],Tp1_id[0:i],'m-.',label=r'$T_1$ identified EB')
        plt.plot(tm[0:i],Tpl_emp1[0:i],'g:',label=r'$T_1$ empirical FOPDT')
        plt.ylabel('T1 (degC)')
        plt.legend(loc='best', fontsize='small', ncol=2)
        
        # 2. T2 Temperature Graph
        ax=plt.subplot(4,1,2)
        ax.grid()
        plt.plot(tm[0:i],T2[0:i],'bx',label=r'$T_2$ measured')
        plt.plot(tm[0:i],Tp2[0:i],'k--',label=r'$T_2$ default EB')
        plt.plot(tm[0:i],Tp2_id[0:i],'c-.',label=r'$T_2$ identified EB')
        plt.plot(tm[0:i],Tpl_emp2[0:i],'c:',label=r'$T_2$ empirical FOPDT')
        plt.ylabel('T2 (degC)')
        plt.legend(loc='best', fontsize='small', ncol=2)
        
        # 3. Cumulative Error Graph
        ax=plt.subplot(4,1,3)
        ax.grid()
        plt.plot(tm[0:i],error_eb[0:i],'k-',label='Default EB Error')
        plt.plot(tm[0:i],error_eb_id[0:i],'m-.',label='Identified EB Error')
        plt.plot(tm[0:i],error_fopdt_emp[0:i],'g:',label='FOPDT Error')
        plt.ylabel('Cumulative Error')
        plt.legend(loc='best', fontsize='small', ncol=3)
        
        # 4. Heaters Graph
        ax=plt.subplot(4,1,4)
        ax.grid()
        plt.plot(tm[0:i],Q1[0:i],'r-',label=r'$Q_1$')
        plt.plot(tm[0:i],Q2[0:i],'b:',label=r'$Q_2$')
        plt.ylabel('Heaters (%)')
        plt.xlabel('Time (sec)')
        plt.legend(loc='best')
        
        plt.draw()
        plt.pause(0.05)

    # Turn off heaters
    a.Q1(0)
    a.Q2(0)
    a.close()

    # Save text file and plot at end
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i])
    # Save figure
    plt.savefig('test_allModels.png')

# Allow user to end loop with Ctrl-C          
except KeyboardInterrupt:
    # Disconnect from Arduino
    a.Q1(0)
    a.Q2(0)
    print('Shutting down')
    a.close()
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i])
    plt.savefig('test_allModels.png')

# Make sure serial connection still closes when there's an error
except:          
    # Disconnect from Arduino
    a.Q1(0)
    a.Q2(0)
    print('Error: Shutting down')
    a.close()
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i])
    plt.savefig('test_allModels.png')
    raise