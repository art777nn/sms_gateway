<template>
  <div class="balance-container">
      <span>{{ balance.dttm }}: <b>{{ balance.balance }}</b> у.е.</span>
  </div>
  
</template>

<script>
export default {
  name: 'balance-block',
  props: {
    balance: Object
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
