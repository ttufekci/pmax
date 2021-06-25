import numpy as np
import math
import talib as ta
from binance.client import Client
import config
import time

def generateVar(high_array, low_array, moving_average_length = 10):

    valpha = 2/(moving_average_length + 1)

    hl2 = (high_array + low_array)/2

    vud1 = []

    before_val = 0

    for current_hl2 in hl2:
        if current_hl2 > before_val:
            vud1.append(current_hl2 - before_val)
        else:
            vud1.append(0)

        before_val = current_hl2

    vdd1 = []

    for current_hl2 in hl2:
        if current_hl2 < before_val:
            vdd1.append(before_val - current_hl2)
        else:
            vdd1.append(0)

        before_val = current_hl2

    vUD = []

    geriden_gelen_indx = 0

    len_vud1 = len(vud1)

    finished = False

    for j in range(1,9):
        window_sum = 0
        for k in range(0,j):
            window_sum = window_sum + vud1[k]
        vUD.append(window_sum)

    while geriden_gelen_indx < len_vud1:
        window_sum = 0
        for i in range(0,9):
            current_indx = geriden_gelen_indx + i
            if current_indx >= len_vud1:
                finished = True
                break
            window_sum = window_sum + vud1[current_indx]
        vUD.append(window_sum)

        if finished:
            break

        geriden_gelen_indx = geriden_gelen_indx + 1

    vUD_ar = np.asarray(vUD[:-1])

    vDD = []

    geriden_gelen_indx = 0

    len_vdd1 = len(vdd1)

    finished = False

    for j in range(1,9):
        window_sum = 0
        for k in range(0,j):
            window_sum = window_sum + vdd1[k]
        vDD.append(window_sum)

    while geriden_gelen_indx < len_vdd1:
        window_sum = 0
        for i in range(0,9):
            current_indx = geriden_gelen_indx + i
            if current_indx >= len_vdd1:
                finished = True
                break
            window_sum = window_sum + vdd1[current_indx]
        vDD.append(window_sum)

        if finished:
            break

        geriden_gelen_indx = geriden_gelen_indx + 1

    vDD_ar = np.asarray(vDD[:-1])

    vCMO = ((vUD_ar - vDD_ar) / (vUD_ar + vDD_ar))

    hl2_left = hl2[:]

    var_before = 0.0

    var = []

    for i in range(0, len(high_array)):
        var_current = (valpha * abs(vCMO[i])*hl2_left[i]) + (1 - valpha*abs(vCMO[i]))*var_before
        var.append(var_current)
        var_before = var_current

    var_arr = np.asarray(var)

    return var_arr

def generateEma(high_array, low_array, moving_average_length = 10):
    hl2 = (high_array + low_array)/2

    ema10 = ta.EMA(hl2, moving_average_length)

    return ema10

def generatePMax(var_array, close_array, high_array, low_array, atr_period, atr_multiplier):

    try:
        atr = ta.ATR(high_array, low_array, close_array, atr_period)
    except Exception as exp:
        print('exception in atr:', str(exp), flush=True)
        return []

    previous_final_upperband = 0
    previous_final_lowerband = 0
    final_upperband = 0
    final_lowerband = 0
    previous_var = 0
    previous_pmax = 0
    pmax = []
    pmaxc = 0

    for i in range(0, len(close_array)):
        if np.isnan(close_array[i]):
            pass
        else:
            atrc = atr[i]
            varc = var_array[i]

            if math.isnan(atrc):
                atrc = 0

            basic_upperband = varc + atr_multiplier * atrc
            basic_lowerband = varc - atr_multiplier * atrc

            if basic_upperband < previous_final_upperband or previous_var > previous_final_upperband:
                final_upperband = basic_upperband
            else:
                final_upperband = previous_final_upperband

            if basic_lowerband > previous_final_lowerband or previous_var < previous_final_lowerband:
                final_lowerband = basic_lowerband
            else:
                final_lowerband = previous_final_lowerband

            if previous_pmax == previous_final_upperband and varc <= final_upperband:
                pmaxc = final_upperband
            else:
                if previous_pmax == previous_final_upperband and varc >= final_upperband:
                    pmaxc = final_lowerband
                else:
                    if previous_pmax == previous_final_lowerband and varc >= final_lowerband:
                        pmaxc = final_lowerband
                    elif previous_pmax == previous_final_lowerband and varc <= final_lowerband:
                        pmaxc = final_upperband

            pmax.append(pmaxc)

            previous_var = varc

            previous_final_upperband = final_upperband

            previous_final_lowerband = final_lowerband

            previous_pmax = pmaxc

    return pmax

if __name__ == '__main__':
    #python binance client objemizi olusturuyoruz.
    client = Client(config.API_KEY, config.API_SECRET)

    # ikilimizi seciyoruz
    pair = 'ETHUSDT'

    # istediğimiz mum sayısını belirliyoruz
    limit = 500

    # zaman araligi, 5 dakikalik grafige bakiyorum
    interval = '5m'

    # ortalama tipi olarak VAR seciyorum.
    ortalama_tipi = 'VAR'

    # ortalama tipi: EMA almak icin asagidaki commenti kaldirip, yukarıdaki var satırını
    # commente alin
    # ortalama_tipi = 'EMA'

    while 1:
        # binance'in limitlerine takilmamak icin, biraz bekliyoruz. 10 saniye kadar.
        time.sleep(10)

        try:
            klines = client.get_klines(symbol=pair, interval=interval, limit=limit)
        except Exception as exp:
            # baglanti hatasi olursa, biraz bekleyip, tekrar yeni client olusturuyor,
            # donguye kaldigim yerden devam ediyorum
            msg = f'exception in get_klines {str(exp)}'
            print(msg, flush=True)
            time.sleep(10)
            client = Client(config.API_KEY, config.API_SECRET)
            continue

        open_time = [int(entry[0]) for entry in klines]
        open_klines = [float(entry[1]) for entry in klines]
        high = [float(entry[2]) for entry in klines]
        low = [float(entry[3]) for entry in klines]
        close = [float(entry[4]) for entry in klines]

        close_array1 = np.asarray(close)
        close_array = close_array1[:-1]

        high_array1 = np.asarray(high)
        high_array = high_array1[:-1]

        low_array1 = np.asarray(low)
        low_array = low_array1[:-1]

        open_array1 = np.asarray(open_klines)
        open_array = open_array1[:-1]

        if ortalama_tipi == 'VAR':

            # Vidya (VAR) hesaplamasini yapiyorum
            var_arr = generateVar(high_array, low_array, moving_average_length=10)

            # Profit maximizer (pmax) hesaplamak icin, bir onceki satirda hesaplamis oldugum
            # var arrayini parametre olarak gonderiyorum
            pmax = generatePMax(var_arr, close_array, high_array, low_array, 10, 3)

            last_var = var_arr[-1]
            previous_var = var_arr[-2]

            last_pmax = pmax[-1]
            previous_pmax = pmax[-2]

            print('last var:', last_var, 'last pmax', last_pmax, flush=True)

            if (last_var > last_pmax and previous_var < previous_pmax):
                msg = f'buy signal for {pair}'
                print(msg, flush=True)

            if last_var < last_pmax and previous_var > previous_pmax:
                msg = f'sell signal for {pair}'
                print(msg, flush=True)


        elif ortalama_tipi == 'EMA':

            # EMA (EMA) hesaplamasini yapiyorum
            ema_arr = generateEma(high_array, low_array, moving_average_length=10)

            # Profit maximizer (pmax) hesaplamak icin, bir onceki satirda hesaplamis oldugum
            # var arrayini parametre olarak gonderiyorum
            pmax = generatePMax(ema_arr, close_array, high_array, low_array, 10, 3)

            last_ema = ema_arr[-1]
            previous_ema = ema_arr[-2]

            last_pmax = pmax[-1]
            previous_pmax = pmax[-2]

            print('last ema:', last_ema, 'last pmax', last_pmax, flush=True)

            if (last_ema > last_pmax and previous_ema < previous_pmax):
                msg = f'buy signal for {pair}'
                print(msg, flush=True)

            if last_ema < last_pmax and previous_ema > previous_pmax:
                msg = f'sell signal for {pair}'
                print(msg, flush=True)


