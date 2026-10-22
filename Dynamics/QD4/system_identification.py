import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
import matplotlib.pyplot as plt

data = np.loadtxt("Dynamics/QD4/data_DataCollection.txt",delimiter=",", skiprows=1)

t_data  = data[:, 0]
u1_data = data[:, 1]
u2_data = data[:, 2]
y1_data = data[:, 3]+273.15
y2_data = data[:, 4]+273.15

##########MODIFY HERE IF THE AMBIENT TEMPERATURE DIFFERED FROM THE TEMPERATURE OF THE HEATERS DURING EXPERIMENTS
Tinf = 19.0
################################################################################################################

def model(t, x, u, p):
    Q1, Q2 = u

    T1, T2 = x
    theta1,theta2,theta3,theta4,theta5,theta6 = p
    sm = 5.67e-8

    dx1 = theta1*(Tinf-T1)+theta2*sm*(Tinf**4-T1**4)+theta3*(T2-T1)+theta4*sm*(T2**4-T1**4)+theta5*Q1
    dx2 = theta1*(Tinf-T2)+theta2*sm*(Tinf**4-T2**4)+theta3*(T1-T2)+theta4*sm*(T1**4-T2**4)+theta6*Q2

    return [dx1, dx2]

def one_step_predict(p, xk, uk):

    sol = solve_ivp(
        model,
        [0,1],
        xk,
        args=(uk, p),
        t_eval=[1],
        method='RK45'
    )

    return sol.y[:, -1]


def residuals(p,s):

    res = []

    for k in range(len(t_data)-1):
        x0 = [y1_data[k],y2_data[k]]
        u0 = [u1_data[k], u2_data[k]]
        x_pred = one_step_predict(
            p,
            x0,
            u0
        )
        x1 = [y1_data[k+1],y2_data[k+1]]

        res.extend(x1 - x_pred)

    res[::2] = np.array(res[::2])/s[0]
    res[1::2] = np.array(res[1::2])/s[1]

    return np.array(res)


def model_sim(t, x, p):

    T1, T2 = x
    theta1,theta2,theta3,theta4,theta5,theta6 = p

    Q1 = u1_fun(t)
    Q2 = u2_fun(t)

    sm = 5.67e-8

    dx1 = theta1*(Tinf-T1)+theta2*sm*(Tinf**4-T1**4)+theta3*(T2-T1)+theta4*sm*(T2**4-T1**4)+theta5*Q1
    dx2 = theta1*(Tinf-T2)+theta2*sm*(Tinf**4-T2**4)+theta3*(T1-T2)+theta4*sm*(T1**4-T2**4)+theta6*Q2

    return [dx1, dx2]

def simulate(p, x0):

    sol = solve_ivp(
        lambda t, x: model_sim(t, x, p),
        (t_data[0], t_data[-1]),
        x0,
        t_eval=t_data,
        method='RK45'
    )

    x = sol.y.T
    y = x
    return y

###########
u1_fun = interp1d(t_data, u1_data,
                  bounds_error=False,
                  fill_value="extrapolate")

u2_fun = interp1d(t_data, u2_data,
                  bounds_error=False,
                  fill_value="extrapolate")

#####################Initial guess for the parameters
p0 = [0.005,   4.5e-4, 0.001, 9e-5,  0.005,    0.00375 ]
values_res = residuals(p0,np.array([1,1]))

scaling = [max(np.abs(values_res[::2])), max(np.abs(values_res[1::2]))]
result_scaled = least_squares(
    lambda p:residuals(p, scaling),
    p0,
    bounds=(0, 1e-2),##1e-2 works
    ftol=1e-15, xtol=1e-15, gtol=1e-15
    )

scaling = [1 ,1]
result = least_squares(
    lambda p:residuals(p, scaling),
    p0,
    bounds=(0, 1e-2),##1e-2 works
    ftol=1e-15, xtol=1e-15, gtol=1e-15
    )

p_cost = result.cost
p_est = result.x

if result_scaled.cost < result.cost:
    p_cost = result_scaled.cost
    p_est = result_scaled.x

print('Parameter estimation.')
print('Initial guess:')
print('  alpha1 alpha2 alpha3 alpha4 alpha5 alpha6')
print('{:6.6f} {:6.6f} {:6.6f} {:6.6f} {:6.6f} {:6.6f}'.format(p0[0], \
                                                       p0[1], \
                                                       p0[2], \
                                                       p0[3], \
                                                       p0[4], \
                                                       p0[5]))
print('Estimated values:')
print('  alpha1 alpha2 alpha3 alpha4 alpha5 alpha6')
print('{:6.6f} {:6.6f} {:6.6f} {:6.6f} {:6.6f} {:6.6f}'.format(p_est[0], \
                                                       p_est[1], \
                                                       p_est[2], \
                                                       p_est[3], \
                                                       p_est[4], \
                                                       p_est[5]))


x0 = [y1_data[0],y2_data[0]]
y0 = simulate(p0, x0)

y_est = simulate(p_est, x0)

plt.figure(figsize=(8, 8))
ax=plt.subplot(2,1,1)
ax.grid()

plt.plot(y1_data,'r--', linewidth=2,label='Measurements')
plt.plot(y0[:,0],':', linewidth=2,label='Initial model')
plt.plot(y_est[:,0], linewidth=2,label='Identified model')

plt.ylabel('Temperature 1 (K)')
plt.xlabel('Time (sec)')
plt.legend(loc='best')

ax=plt.subplot(2,1,2)
ax.grid()
plt.plot(y2_data,'r--', linewidth=2,label='Measurements')
plt.plot(y0[:,1],':', linewidth=2,label='Initial model')
plt.plot(y_est[:,1], linewidth=2,label='Identified model')
plt.legend(loc='best')

plt.ylabel('Temperature 2 (K)')
plt.xlabel('Time (sec)')

plt.savefig('test_comparison.png')


plt.figure(figsize=(8, 8))
ax=plt.subplot(2,1,1)
ax.grid()

N = len(t_data)
error1 = 1/N*(y0[:,0]-y1_data)**2
error1_est = 1/N*(y_est[:,0]-y1_data)**2

rmse_initial_t1 = np.sum(error1)**0.5
rmse_estimated_t1 = np.sum(error1_est)**0.5

plt.plot(error1,'b', linewidth=2,label='T1 error default')
plt.plot(error1_est,'r--', linewidth=2,label='T1 error estimation')
plt.ylabel('Temperature 1 error (K)')
plt.xlabel('Time (sec)')
plt.legend(loc='best')

ax=plt.subplot(2,1,2)
ax.grid()
error2 = 1/N*(y0[:,1]-y2_data)**2
error2_est = 1/N*(y_est[:,1]-y2_data)**2

rmse_initial_t2 = np.sum(error2)**0.5
rmse_estimated_t2 = np.sum(error2_est)**0.5

print('Error values (RMSE):')
print('  Initial T1, Initial T2,  Estimated T1, Estimated T2 ')
print('{:6.1f} {:6.2f} {:6.2f} {:6.2f} '.format(rmse_initial_t1, \
                                                       rmse_initial_t2, \
                                                       rmse_estimated_t1, \
                                                       rmse_estimated_t2))

plt.plot(error2,'b', linewidth=2,label='T2 error default')
plt.plot(error2_est,'r--', linewidth=2,label='T2 error estimation')
plt.xlabel('Time (sec)')

plt.legend(loc='best')

plt.ylabel('Temperature 2 error (K)')
plt.xlabel('Time (sec)')
#plt.show()

plt.savefig('test_errors.png')
