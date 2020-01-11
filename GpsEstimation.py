
# importar librerias necesarias
import pandas as pd  # importa la libreria pandas y la nombra como pd
import matplotlib.pyplot as plt  # importa la libreria para hacer graficas
import numpy as np
from numpy.linalg import inv
import math
import utm

datosReales = pd.read_csv('Ruta2Real.csv',
                          header=0)  # importa el archivo .csv e indica que el encabezado esta en la fila 0
datosGPS = pd.read_csv('Ruta2.csv',
                       header=0)  # importa el archivo .csv e indica que el encabezado esta en la fila 0
lonReal = datosReales['lon']
latReal = datosReales['lat']
lonMed = datosGPS['lon']
latMed = datosGPS['lat']
V_Real = datosGPS['speed']  # velocidad real
V_Medida = []  # velocidad medida
grapmedx = []
grapmedy = []
Pos_Real_X = []  # posicion real de x en metros
Pos_Real_Y = []  # posicion real de y en metros
graprealx = []
graprealy = []
Grap_V_real = []

v_est = []
px_est = []
py_est = []


def BEARING(lat1, lon1, lat2, lon2):
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    lon1 = math.radians(lon1)
    lon2 = math.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    R = 6372.795477598
    a = (math.sin(dlat / 2)) ** 2 + math.cos(lat1) * math.cos(lat2) * (math.sin(dlon / 2)) ** 2
    distancia = 2 * R * math.asin(math.sqrt(a))
    distancia = distancia * 1000
    x = math.sin(dlon) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    track_angle = math.atan2(x, y)
    track_angle = math.degrees(track_angle)
    compass_bearing = (track_angle + 360) % 360
    posX = distancia * math.cos(track_angle)
    posY = distancia * math.sin(track_angle)
    return distancia


def GEOTOUTM():
    for i in np.arange(0, len(lonMed)):
        (x, y, zonanumber, zonaletter) = utm.from_latlon(latMed.ix[i], lonMed.ix[i])
        grapmedx.append(x)
        grapmedy.append(y)

    for i in np.arange(0, len(lonReal)):
        (x, y, zonanumber, zonaletter) = utm.from_latlon(latReal.ix[i], lonReal.ix[i])
        Pos_Real_X.append(x)
        Pos_Real_Y.append(y)


def GRAFICAS():
    plt.plot(grapmedx, grapmedy, '.-', label='Mediciones')
    plt.plot(graprealx, graprealy, '-', label='Ruta Real')
    plt.plot(px_est, py_est, '-', label='Estimacion')
    plt.xlabel('X (m)')  # nombra el eje x
    plt.ylabel('Y (m)')  # nombra el eje y
    plt.title('Position')  # pone titulo a la grafica
    plt.legend()
    plt.show()

    plt.clf()
    plt.plot(V_Medida, '-', label='Velocidad Medida')
    plt.plot(Grap_V_real, '-', label='Velocidad Real')
    plt.plot(v_est, '-', label='Estimacion')
    plt.xlabel('Muestras')  # nombra el eje x
    plt.ylabel('V (m/s)')  # nombra el eje y
    plt.title('Velocity')  # pone titulo a la grafica
    plt.legend()
    plt.show()

def kf_predict(X, P, A, Q, B, U):
    X = np.dot(A, X) + np.dot(B, U)
    P = np.dot(np.dot(A, P), A.T) + Q
    return X, P

def kf_update(X, P, Y, H, R):
    V = Y - np.dot(H, X)
    S = R + np.dot(np.dot(H, P), H.T)
    K = np.dot(np.dot(P, H.T), inv(S))
    X = X + np.dot(K, V)
    P = np.dot(P, (I - np.dot(K, H)))
    return X, P



GEOTOUTM()
N_iter = 100
dt = 1.0/N_iter
# aceleracion en x e y
ax = 0.0
ay = 0.0
m = (Pos_Real_Y[1] - Pos_Real_Y[0]) / (Pos_Real_X[1] - Pos_Real_X[0])  # calculo de la pendiente
ang = math.atan(m)  # calculo del angulo (respuesta en radianes)
px = Pos_Real_X[0]  # posicion inicial x
py = Pos_Real_Y[0]  # posicion inicial y

# espacio de estados
A = np.array([[1.0, 0.0, dt, 0.0], [0.0, 1.0, 0.0, dt], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
X = np.array([[Pos_Real_X[0]], [Pos_Real_Y[0]], [0.0], [0.0]])  # condiciones iniciales
B = np.array([[dt ** 2 / 2.0, 0.0], [0.0, dt ** 2 / 2.0], [dt, 0.0], [0.0, dt]])
U = np.array([[ax], [ay]])  # vector de entrada ax y ay(aceleraciones en x e y)
W = 0  # ruido en la medicion
V = 0 #ruido en el proceso
#P = 0.1   # covarianza
#Q = np.diag((0.0071, 0.0081, 0.0003, 0.0326)) # covarianza de ruido en el proceso
Q = 0.00001
P = np.diag((0.1, 0.1, 0.1, 0.1))
#Q = np.dot(B, B.T)
Z = 0  # ruido en la medicion
#R = np.eye(4)
#R = np.diag((20, 20, 20, 20))
H = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
I = np.identity(4)


# calculos luego de las mediciones
for i in np.arange(1, len(lonMed)):
    Exactitud = datosGPS['accuracy'].ix[i]
    R = np.diag(((Exactitud)**2,(Exactitud)**2,(Exactitud)**2,(Exactitud)**2))
    if Pos_Real_Y[1] < Pos_Real_Y[0]:

        vx = -V_Real[i] * math.cos(ang) # calculo la velocidad en x
        vy = -V_Real[i] * math.sin(ang) # calculo la velocidad en y

        ax = -(V_Real[i] - V_Real[i - 1]) * math.cos(ang) * dt #calculo la aceleracion en x
        ay = -(V_Real[i] - V_Real[i - 1]) * math.sin(ang) * dt # calculo la aceleracion en y
    else:
        vx = V_Real[i] * math.cos(ang)  # calculo la velocidad en x
        vy = V_Real[i] * math.sin(ang)  # calculo la velocidad en y

        ax = (V_Real[i] - V_Real[i - 1]) * math.cos(ang) * dt  # calculo la aceleracion en x
        ay = (V_Real[i] - V_Real[i - 1]) * math.sin(ang) * dt  # calculo la aceleracion en y

    d_med = BEARING(latMed[i - 1], lonMed[i - 1], latMed[i], lonMed[i])
    v_med = d_med / 1

    mx = grapmedx[i]    #posicion medida
    my = grapmedy[i]    #posicion medida
    Y = np.array([[mx], [my], [0], [0]])

    U = np.array([[ax], [ay]])

    # aplicando el filtro de kalman
    for j in np.arange(0, N_iter):
        Grap_V_real.append(V_Real[i])
        V_Medida.append(v_med)

        px = px + vx * dt  # posicion x real
        py = py + vy * dt  # posicion y real
        X = np.array([[px], [py], [vx], [vy]])
        graprealx.append(X[0])  # vector para graficar posicion real x
        graprealy.append(X[1])  # vector para graficar posicion real y
        (X, P) = kf_predict(X, P, A, Q, B, U)
        (X, P) = kf_update(X, P, Y, H, R)
        px_est.append(X[0])
        py_est.append((X[1]))
        v_est.append((math.sqrt(X[2]**2+X[3]**2)))

GRAFICAS()