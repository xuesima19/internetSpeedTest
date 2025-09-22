import speedtest
import time
import pickle
import os

def best_by_throughput(top_n=3):
    st = speedtest.Speedtest(secure=True, timeout=20)
    # Rank by latency first
    lat_ranked = []
    for s in st.get_closest_servers()[:20]:
        try:
            st.get_servers([s['id']])
            chosen = st.get_best_server()
            lat = chosen.get('latency', None)
            if lat is not None:
                lat_ranked.append((lat, chosen))
        except speedtest.SpeedtestException:
            pass

    lat_ranked.sort(key=lambda x: x[0])
    top = [srv for _, srv in lat_ranked[:top_n]]

    results = []
    for srv in top:
        try:
            st.get_servers([srv['id']])
            st.get_best_server()
            down = st.download(threads=1)
            up = st.upload(threads=1)
            results.append((srv, down, up))
        except speedtest.SpeedtestException:
            pass

    # Pick best by download throughput
    if results:
        srv, down, up = max(results, key=lambda x: x[1])
        return srv['id']
    return None

def test_server(server_id):
    st = speedtest.Speedtest(secure=True, timeout=20)
    st.get_servers([server_id])
    best = st.get_best_server()
    ids = best.get('id')
    sponsor = best.get('sponsor')
    name = best.get('name')
    host = best.get('host')
    latency = best.get('latency')
    
    return ids, sponsor, name, host, latency

def run_speed_test(Server_ID):
    """
    Performs an internet speed test and prints the results.
    """
    try:
        print(f"Finding best server for {Server_ID}...")
        try:
            if Server_ID is None:
                raise speedtest.SpeedtestException("No Server ID currently available")
            
            st = speedtest.Speedtest(secure=True, timeout=20)

            st.get_servers([Server_ID])
            best = st.get_best_server()

            print(f"Server {Server_ID}: {best['sponsor']} ({best['name']})")

            print("Testing latency...")
            # after best = st.get_best_server()
            resolved_id = int(best.get('id')) if best.get('id') is not None else Server_ID

            # latency may be missing on some entries
            latency = best.get('latency')
            if latency is None:
                try:
                    # quick re-ping via best selection to populate ping if needed
                    latency = st.results.ping
                except Exception:
                    latency = None
            print(f"Latency: {latency} ms")

            print("Testing download speed...")
            download_speed_bps = st.download()
            download_speed_mbps = round(download_speed_bps / (10**6), 2)
            print(f"Download Speed: {download_speed_mbps} Mbps")

            print("Testing upload speed...")
            upload_speed_bps = st.upload()
            upload_speed_mbps = round(upload_speed_bps / (10**6), 2)
            print(f"Upload Speed: {upload_speed_mbps} Mbps")

            print("Testing ping...")
            ping = st.results.ping  # ms measured during tests
            print(f"Ping: {ping} ms")

            results = {
                'timestamp': time.time(),
                'timestamp_iso': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime()),
                'server_id_requested': Server_ID,
                'server_id_resolved': resolved_id,
                'server_sponsor': best.get('sponsor'),
                'server_name': best.get('name'),
                'server_host': best.get('host'),
                'latency': latency,
                'download_speed_mbps': download_speed_mbps,
                'upload_speed_mbps': upload_speed_mbps,
                'ping': ping
            }
            save_results(results)
        except speedtest.SpeedtestException as e:
            print(f"An error occurred during the speed test: {e}")
            results = {
                'timestamp': time.time(),
                'timestamp_iso': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime()),
                'server_id_requested': Server_ID,
                'server_id_resolved': None,
                'server_sponsor': None,
                'server_name': None,
                'server_host': None,
                'latency': None,
                'download_speed_mbps': None,
                'upload_speed_mbps': None,
                'ping': None
            }
            save_results(results)
                
        
    except speedtest.SpeedtestException as e:
        print(f"An error occurred during the speed test: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def save_results(results):
    os.makedirs('./Logs', exist_ok=True)
    with open('./Logs/internet_speed_results.pickle', 'ab') as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    try:
        interval = 60*30 # 30 minutes
        while True:
            start_time = time.time()
            
            print("current time: ", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            print("Finding server with best latency...")
            for i in range(3):
                Server_ID = best_by_throughput()
                if Server_ID is not None:
                    break
                time.sleep(10)
            run_speed_test(Server_ID)
            print("Speed test completed.")
            
            next_run = start_time + interval
            delay = max(0, next_run - time.time())
            time.sleep(delay)
    except KeyboardInterrupt:
        print("Stopped by user.")
