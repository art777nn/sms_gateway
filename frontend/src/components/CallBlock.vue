<template>
  <div class="container">

    <div v-for="m in calls" :key="m.created_at" class="message">
      <div class="header">
        <span>{{ m.created_at }}</span>
      </div>
      <div class="text"> 
 
        <span>
          {{ m.caller }}
        </span>
      </div>

      <audio controls :src=get_record_url(m.id)></audio>
    </div>
  </div>
</template>

<script>
export default {
  name: 'call-block',
  props: {
    calls: Array,
  },
  data() {
    return {
      isCopied: false, // Флаг для уведомления
      code: ''
    }
  },
  methods: {
    highlightNumbers(text) {
      return text.replace(/(\d+)/g, '<span @click=copy2Clipboard(this) class="highlighted">$1</span>')
    },
    copy2Clipboard(text) {
          navigator.clipboard.writeText(text).then(() => {
            console.log('Текст скопирован в буфер обмена:', text);
            this.isCopied = true; // Показываем уведомление
            this.code = text
            setTimeout(() => {
              this.isCopied = false; // Скрываем уведомление через 2 секунды
            }, 4000);
        }, function(err) {
            console.error('Не удалось скопировать текст: ', err);
        });     
    },
    textParts(text) {
      // Разделяем текст на части по пробелам, сохраняем числа и текст отдельно
      return text.match(/(\d+|\D+)/g) || []; // Сохраняем числа и текст
    },
    isNumber(part) {
      return !isNaN(part); // Проверяем, является ли часть числом
    },
    get_record_url(id) {
      return `/records/${id}.wav`
    }
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
.highlighted {
    background-color: #347236;
    padding: 4px;
    cursor: pointer;
}

.notification {
  background-color: #347236;
  color: white;
  border-radius: 5px;
  transition: opacity 0.5s;
}

.notification-block { 
  padding: 20px;
  height: 24px;
  display: flex;
}
</style>
