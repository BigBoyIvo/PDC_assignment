import tclab
import time

try:
    # Connect to Arduino
    a = tclab.TCLab()

    # Get Version
    print(a.version)

    # Turn LED on
    print('LED On')
    a.LED(100)

    # Taper LED off
    for i in range(100,-1,-10):
        print('LED Power ' + str(i))
        time.sleep(0.5)
        a.LED(i)

    print('LED Off')
    a.LED(0)
    a.close()

# Allow user to end loop with Ctrl-C           
except KeyboardInterrupt:
    # Disconnect from Arduino
    a.Q1(0)
    a.Q2(0)
    print('Shutting down')
    a.close()
    
# Make sure serial connection still closes when there's an error
except:           
    # Disconnect from Arduino
    a.Q1(0)
    a.Q2(0)
    print('Error: Shutting down')
    a.close()
    raise
