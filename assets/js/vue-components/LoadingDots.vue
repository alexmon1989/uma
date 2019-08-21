<template>
    <span>{{ dots }}</span>
</template>

<script>
    export default {
        name: "LoadingDots",
        data() {
            return {
                count: 0
            }
        },
        computed: {
            dots: function () {
                return Array(this.count + 1).join(".");
            }
        },
        mounted() {
            const self = this;
            setInterval(function() {
                self.count = ++self.count % 4;
            }, 1000);
        },
    }
</script>

<style scoped>

</style>