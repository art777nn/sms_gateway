<template>
  <div class="signal" :title="signal_dttm">
    <div :class='["signal-bars", "mt1", "sizing-box", get_signal_class()]'>
      <div class="first-bar bar"></div>
      <div class="second-bar bar"></div>
      <div class="third-bar bar"></div>
      <div class="fourth-bar bar"></div>
      <div class="fifth-bar bar"></div>
    </div>
  </div>
  
</template>

<script>
export default {
  name: 'gsm-signal',
  props: {
    signal: Number,
    signal_dttm: String
  },
  methods: {
    get_signal_class() {
      if ( this.signal > 0 && this.signal < 2) 
        return "bad one-bar"

      if ( this.signal >= 2 && this.signal < 3) 
        return "bad two-bars"

      if ( this.signal >= 3 && this.signal < 4) 
        return "ok three-bars"

      if ( this.signal >= 4 && this.signal < 4.5) 
        return "good four-bars"

      if ( this.signal >= 4.5) 
        return "good five-bars"

      return 'bad zero-bar'
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
* { 
  box-sizing: border-box; 
}
.sizing-box {
  height: 32px;;
  width: 32px;;
}

.signal-bars {
  display: inline-block;
}

.signal-bars .bar {
  width: 14%;
  margin-left: 4%;
  min-height: 20%;
  display: inline-block;
}
.signal-bars .bar.first-bar  { height: 20%; }
.signal-bars .bar.second-bar { height: 40%; }
.signal-bars .bar.third-bar  { height: 60%; }
.signal-bars .bar.fourth-bar { height: 80%; }
.signal-bars .bar.fifth-bar  { height: 99%; }

.good .bar {
  background-color: #16a085;
  border: thin solid darken(#16a085, 7%);
}
.bad .bar {
  background-color: #e74c3c;
  border: thin solid darken(#e74c3c, 20%);
}
.ok .bar {
  background-color: #f1c40f;
  border: thin solid darken(#f1c40f, 7%);
}

.four-bars .bar.fifth-bar,
.three-bars .bar.fifth-bar,
.three-bars .bar.fourth-bar,
.one-bar .bar:not(.first-bar),
.two-bars .bar:not(.first-bar):not(.second-bar) {       background-color: #fafafa;
  border: thin solid #f3f3f3;
}
</style>
