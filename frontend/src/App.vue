<template>
  <div class="main">
    <div class="operator"> <div>{{ operator }} {{ signalType }} </div><signal :signal_dttm="signal_dttm" :signal="signal"></signal></div>
    <div :title="balance_dttm"><span>*105#:</span> {{ prep_balance(balance) }}</div>
    <div class="data">
      <call-block :load="is_loading" :calls="calls"/>
      <sms-block :load="is_loading" :messages="messages"/>
    </div>
    
  </div>
</template>

<script>
import SmsBlock from './components/SmsBlock.vue'
import CallBlock from './components/CallBlock.vue'
import Signal from './components/Signal.vue'

export default {
  name: 'App',
  components: {
    SmsBlock,
    CallBlock,
    Signal
  },
  data() {
    return {
      messages: [],
      balance: "",
      balance_dttm: '',
      operator: "",
      signalType: "0G",
      signalTypeDttm: "",
      signal: 1,
      signal_dttm: '',
      calls: [],
      is_loading: false,
    };
  },
  methods: {
    get_data() { 
      this.is_loading = true
      fetch('http://192.168.1.36:8000/get-sms?limit=5', {
        method: "GET"
      }).then((response) =>{
          response.json().then((data) => {
            this.messages = data
            this.is_loading = false
          })
      }).catch(() => {
        this.is_loading = false
      })
    },
    get_balance() {
      fetch('http://192.168.1.36:8000/get-balance', {
        method: "GET"
      }).then((response) =>{
          response.json().then((data) => {
            if (data) {
              this.balance = data?.data?.message
              this.balance_dttm = data?.updated_at
            }
          })
      })
    },
    get_operator() {
      fetch('http://192.168.1.36:8000/get-operator', {
        method: "GET"
      }).then((response) =>{
          response.json().then((data) => {
            if (data) {
              this.operator = data?.data?.value
            }
          })
      })
    },
    get_signal() {
      fetch('http://192.168.1.36:8000/get-signal', {
        method: "GET"
      }).then((response) =>{
          response.json().then((data) => {
            if (data) {
              this.signal = data?.data?.level
              this.signal_dttm = data?.updated_at
            }
          })
      })
    },
    get_signal_type() {
      fetch('http://192.168.1.36:8000/get-signal-type', {
        method: "GET"
      }).then((response) =>{
          response.json().then((data) => {
            if (data) {
              this.signalType = data?.data?.type
              this.signalTypeDttm = data?.updated_at
            }
          })
      })
    },
    get_calls() {
      fetch('http://192.168.1.36:8000/get-calls?limit=5', {
        method: "GET"
      }).then((response) =>{
          response.json().then((data) => {
            if (data) {
              this.calls = data
            }
          })
      })
    },
    prep_balance(text) {
      return text.split('. ')[0]
    }
  },
  beforeMount() {
    
    this.get_balance()
    this.get_data()
    this.get_calls()
    this.get_operator()
    this.get_signal()
    this.get_signal_type()
    setInterval(()=>{  
      this.get_data() 
      this.get_calls()
    }, 5000)
    setInterval(()=>{  
      this.get_operator()
      this.get_balance()
      this.get_signal()
      this.get_signal_type()
    }, 30000)
  },
}
</script>

<style>
body {
  background-color: #424447;

}
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #dddddd;
  margin-top: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.message {
  border: 1px solid rgb(44, 44, 44);
}
.message:hover {
  background-color: #565657;
}
.header{
 text-align: left;
 padding: 8px;
}
.text {
 text-align: left;
 padding: 8px;
 word-break: break-all; 
}
.balance-container {
  margin-bottom: 24px;
}
.data {
  display: flex;
}
.container {
  margin: 16px;
  max-width: 50%;
  width: 50%;
}
.operator {
  display: flex;
  justify-content: center;
  align-items: end;
}
</style>
