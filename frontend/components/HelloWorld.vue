<template>
  <div class="container">
    <h1>Hello world!</h1>
    <div class="input-container">
      <input v-model="userText" type="text" placeholder="Type something here..." />
    </div>
    <div v-if="userText" class="output-container">
      <p>{{ userText }}</p>
    </div>
  </div>
</template>

<script setup>
const userText = ref("");
</script>

<style scoped>
.container {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  max-width: 600px;
  margin: 100px auto;
  padding: 20px;
  text-align: center;
}

h1 {
  margin-bottom: 30px;
  color: #333;
}

.input-container {
  margin-bottom: 20px;
}

input {
  width: 100%;
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.output-container {
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 4px;
  text-align: left;
  word-wrap: break-word;
}
</style>
