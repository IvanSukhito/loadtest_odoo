import json
import re
from locust import HttpUser, task, constant, TaskSet, SequentialTaskSet
from bs4 import BeautifulSoup

class WebShop(SequentialTaskSet):

    csrf_token = None  
    
    def get_csrf_token(self):
        """Mengambil CSRF Token dari JavaScript."""
        if self.csrf_token:
            return self.csrf_token 
        
        response = self.client.get("/event/theme-park-1/register")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            script_tag = soup.find("script", {"id": "web.layout.odooscript"})
            if script_tag:
                match = re.search(r'csrf_token:\s*"([^"]+)"', script_tag.text)
                if match:
                    self.csrf_token = match.group(1)
                    return self.csrf_token

        print(f"❌ Gagal mendapatkan CSRF Token: {response.status_code}")
        return None

        
    @task()
    def get_event(self):
        self.client.cookies.clear()
        self.client.get('/event')

    @task()
    def detail_event(self):
        ''' Direct Ke Detail Event'''
        self.client.cookies.clear()
        response = self.client.get("/event/theme-park-1/register")

        if response.status_code == 200:
            print("✅ Halaman event berhasil dimuat.")
        else:
            print(f"❌ Gagal mengakses event. Status code: {response.status_code}")

    @task()
    def register_event(self):
        ''' Register Event Pertama'''
        payload = {
            "id": 0,
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "nb_register-1": "1",
                "nb_register-3": "0",
                "nb_register-4": "0",
                "nb_register-5": "0",
                "nb_register-6": "0"
            }
        }

        url = "/event/theme-park-1/registration/new"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        response = self.client.post(url, json=payload, headers=headers, catch_response=True)
        
        if response.status_code == 200:
            print(f"✅ Pendaftaran berhasil")
        else:
            print(f"❌ Pendaftaran gagal: {response.status_code}")

    @task()
    def confirm_order(self):
        ''' Confirm Order '''
        url = "/event/theme-park-1/registration/confirm"
        csrf_token = self.get_csrf_token()
    
        if not csrf_token:
            print("🚨 CSRF token tidak ditemukan.")
            return

        payload = {
            "csrf_token": csrf_token,
            "1-name-1": "Lukman Hakim",
            "1-email-2": "ivan.sukhito28@gmail.com",
            "1-phone-3": "082122544418",
            "1-event_ticket_id": "1",
            "recaptcha_token_response": "undefined"
        }

        response = self.client.post(url, data=payload)
        if response.status_code == 200:
            print(f"✅ Sukses Confirm Order berhasil")
        else:
            print(f"❌ Pendaftaran alamat gagal: {response.status_code}")

    @task()
    def access_shop_address(self):
        self.client.get("/shop/address")

    @task()
    def submit_address(self):
        """Kirim detail checkout"""
        url = "/shop/address/submit"
        csrf_token = self.get_csrf_token()
        if not csrf_token:
            print("🚨 CSRF token tidak ditemukan.")
            return

        payload = {
            "email": "testuser@example.com",
            "name": "Layani.id",
            "phone": "+628123456789",
            "company_name": "testing",
            "vat": "",
            "street": "Jalan Sudirman No. 1",
            "street2": "",
            "city": "Kab. Kaur",
            "zip": "129101",
            "country_id": 100,
            "state_id": 617,
            "csrf_token": csrf_token,
            "address_type": "billing",
            "use_delivery_as_billing": "",
            "required_fields": "name,country_id"
        }


        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = self.client.post(url, data=payload, headers=headers)

        if response.status_code == 200:
            print("✅ Berhasil submit alamat")
        else:
            print(f"❌ Gagal, status code: {response.status_code}")
    
    @task()
    def access_shop_cofirm(self):
        ''' Akses halaman alamat confirm order '''
        self.client.get("/shop/confirm_order")
    
    @task()
    def access_shop_payment(self):
        ''' Masuk Ke Payment '''
        self.client.get("/shop/payment")
        

    def get_payment_data(self, data_attr):
        ''' Dapatkan data dari form pembayaran berdasarkan atribut yang diminta '''
        response = self.client.get("/shop/payment")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            form = soup.find("form", {"id": "o_payment_form"})

            if form:
                data_value = form.get(data_attr)
                print(f"{data_attr}: {data_value}")
                return data_value

        print(f"❌ Gagal mendapatkan {data_attr}: {response.status_code}")
        return None

    @task()
    def simulate_transaction_payment(self):
        ''' Mulai Simulasi Transaction Payment '''
        url = self.get_payment_data("data-transaction-route")
        csrf_token = self.get_csrf_token()

        if not csrf_token:
            print("🚨 CSRF token tidak ditemukan.")
            return
        
        access_token = self.get_payment_data("data-access-token")
        headers = {"Content-Type": "application/json"}

        payload = {
            "id": 0,
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "provider_id": 6,
                "payment_method_id": 202,
                "token_id": None,
                "flow": "direct",
                "tokenization_requested": True,
                "landing_route": "/shop/payment/validate",
                "is_validation": False,
                "access_token": access_token,
                "csrf_token": csrf_token
            }
        }
        
        response = self.client.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            print(f"✅ Payment Successful {url} {access_token}: {response.json()}")
        else:
            print(f"❌ Payment Transaction Failed: {response.status_code}, Response: {response.text}")

    @task()
    def access_payment_validate(self):
        ''' Lanjut ke validate payment '''
        self.client.get("/shop/payment/validate")
    
    def simulate_order_payment(self):
        ''' Dapatin dulu Order referencesnya '''
        response = self.client.get("/shop/confirmation")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            match = re.search(r'Order\s*(S\d+)', soup.get_text())

            if match:
                order_reference = match.group(1)
                print(f"✅{order_reference}")
                return order_reference 

            else:
                print("❌ Order Reference tidak ditemukan.")

    @task()
    def simulate_payment(self):
        ''' Lanjut Simulate Payment '''
        url = "/payment/demo/simulate_payment"
        csrf_token = self.get_csrf_token()
        print(csrf_token)
        if not csrf_token:
            print("🚨 CSRF token tidak ditemukan.")
            return

        order_reference = self.simulate_order_payment()
        if not order_reference:
            print(f"Tidak di temukan")
            return

        headers = {"Content-Type": "application/json"}

        payload = {
             "id": 1,
             "jsonrpc": "2.0",
             "method": "call",
             "params": {
                 "reference": order_reference,
                 "payment_details": "1200 1298 1209 1200",
                 "simulated_state": "done"
             }
         }
 
        response = self.client.post(url, headers=headers, data=json.dumps(payload))
 
        if response.status_code == 200:
             print(f"✅ Payment Simulated for {order_reference}: {response.json()}")
        else:
             print(f"❌ Failed to Simulate Payment for {order_reference}")

    @task()
    def poll_payment_status(self):
        url = "/payment/status/poll"
        csrf_token = self.get_csrf_token()
        if not csrf_token:
            print("🚨 CSRF token tidak ditemukan.")
            return

        payload = {
            "id": 0,
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "csrf_token": csrf_token
            }
        }

        headers = {"Content-Type": "application/json"}
        response = self.client.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"✅ Polling Status Berhasil: {response.json()}")
        else:
            print(f"❌ Polling Status Gagal: {response.status_code}, Response: {response.text}")

class RunMyLoadTest(HttpUser):

    host = "http://128.199.111.193:8069"  
    wait_time = constant(5)
    weight = 5
    tasks = [WebShop]

