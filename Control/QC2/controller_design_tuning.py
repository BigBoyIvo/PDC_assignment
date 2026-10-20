import tclab
import numpy as np
import time
import matplotlib.pyplot as plt
from scipy.integrate import odeint

alpha1 = 0.003660
alpha2 = 0
alpha3 = 0.001810
alpha4 = 0
alpha5 = 0.003194
alpha6 = 0.001565

sigma = 5.67e-8
T_amb_C = 18.5
T_amb_K = T_amb_C + 273.15

def nonlinear_model(T, t, Q1, Q2):
    T1_k, T2_k = T
    dT1dt = (alpha1 * (T_amb_K - T1_k) + 
             alpha2 * sigma * (T_amb_K**4 - T1_k**4) + 
             alpha3 * (T2_k - T1_k) + 
             alpha4 * sigma * (T2_k**4 - T1_k**4) + 
             alpha5 * Q1)
             
    dT2dt = (alpha1 * (T_amb_K - T2_k) + 
             alpha2 * sigma * (T_amb_K**4 - T2_k**4) - 
             alpha3 * (T2_k - T1_k) - 
             alpha4 * sigma * (T2_k**4 - T1_k**4) + 
             alpha6 * Q2)
    return [dT1dt, dT2dt]

def on_off_control(sp, pv):
    if pv < sp:
        return 100.0
    else:
        return 0.0

def save_txt(t, u1, u2, y1, y2, sp1, sp2):
    data = np.vstack((t, u1, u2, y1, y2, sp1, sp2))
    data = data.T 
    top = ('Time (sec), Heater 1 (%), Heater 2 (%), ' 
           'Temperature 1 (degC), Temperature 2 (degC), '
           'Set Point 1 (degC), Set Point 2 (degC)')
    np.savetxt('data.txt', data, delimiter=',', header=top, comments='')

a = tclab.TCLab()
print('LED On')
a.LED(100)

run_time = 15.0
loops = int(60.0 * run_time)
tm = np.zeros(loops)

Tsp1 = np.ones(loops) * 18.5
Tsp1[60:] = 40.0
Tsp1[300:] = 30.0
Tsp1[580:] = 60.0

Tsp2 = np.ones(loops) * T_amb_C 

T1 = np.ones(loops) * a.T1 
T2 = np.ones(loops) * a.T2 

T1_model_C = np.ones(loops) * T_amb_C
T2_model_C = np.ones(loops) * T_amb_C
Q1_model = np.zeros(loops)

Q1 = np.zeros(loops) 
Q2 = np.zeros(loops)

print('Running On-Off Control Test. Ctrl-C to end.')
print('  Time     SP     PV_Model  PV_Real    Q1_Real')
print(('{:6.1f} {:6.2f} {:6.2f}    {:6.2f} {:6.2f}').format(tm[0], Tsp1[0], T1_model_C[0], T1[0], Q1[0]))

plt.figure(figsize=(10, 8))
plt.ion()
plt.show()

start_time = time.time()
prev_time = start_time
dt_error = 0.0

T_model_state_K = [T_amb_K, T_amb_K]

try:
    for i in range(1,loops):
        sleep_max = 1.0
        sleep = sleep_max - (time.time() - prev_time) - dt_error
        if sleep>=1e-4:
            time.sleep(sleep-1e-4)
        else:
            time.sleep(1e-4)

        t = time.time()
        dt = t - prev_time
        if (sleep>=1e-4):
            dt_error = dt-1.0+0.009
        else:
            dt_error = 0.0
        prev_time = t
        tm[i] = t - start_time
                    
        T1[i] = a.T1
        T2[i] = a.T2

        Q1[i] = on_off_control(Tsp1[i], T1[i])
        Q1_model[i] = on_off_control(Tsp1[i], T1_model_C[i-1])
        
        t_span = [0, dt]
        T_sim = odeint(nonlinear_model, T_model_state_K, t_span, args=(Q1_model[i], 0.0))
        T_model_state_K = T_sim[-1]
        T1_model_C[i] = T_model_state_K[0] - 273.15
        T2_model_C[i] = T_model_state_K[1] - 273.15

        a.Q1(Q1[i])
        a.Q2(Q2[i])

        print(('{:6.1f} {:6.2f} {:6.2f}    {:6.2f} {:6.2f}').format(tm[i], Tsp1[i], T1_model_C[i], T1[i], Q1[i]))

        # 5. Plotting
        plt.clf()
        ax=plt.subplot(2,1,1)
        ax.grid()
        plt.plot(tm[0:i], T1[0:i], 'r-', label=r'True Setup $T_1$')
        plt.plot(tm[0:i], T1_model_C[0:i], 'g--', linewidth=2, label=r'Nonlinear Model $T_1$')
        plt.plot(tm[0:i], Tsp1[0:i], 'k:', label=r'Set Point')
        plt.ylabel('Temperature (degC)')
        plt.legend(loc='best')
        
        ax=plt.subplot(2,1,2)
        ax.grid()
        plt.step(tm[0:i], Q1[0:i], 'b-', where='post', label=r'Real Setup $Q_1$ (%)')
        plt.step(tm[0:i], Q1_model[0:i], 'g--', alpha=0.5, where='post', label=r'Model $Q_1$ (%)')
        plt.ylabel('Heater Input (%)')
        plt.xlabel('Time (sec)')
        plt.legend(loc='best')
        plt.draw()
        plt.pause(0.05)

    a.Q1(0)
    a.Q2(0)
    a.close()
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i],Tsp1[0:i],Tsp2[0:i])
    plt.savefig('test_OnOff_QC2.png')
        
except KeyboardInterrupt:
    a.Q1(0)
    a.Q2(0)
    print('Shutting down')
    a.close()
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i],Tsp1[0:i],Tsp2[0:i])
    plt.savefig('test_OnOff_QC2.png')
    
except:           
    a.Q1(0)
    a.Q2(0)
    print('Error: Shutting down')
    a.close()
    save_txt(tm[0:i],Q1[0:i],Q2[0:i],T1[0:i],T2[0:i],Tsp1[0:i],Tsp2[0:i])
    plt.savefig('test_OnOff_QC2.png')
    raise
