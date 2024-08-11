<template>
    <div class="pricing">
        <h1>Pricing</h1>
        <p>Choose the plan that suits your needs:</p>
        <ul>
            <li>Basic: Free</li>
            <li>Pro: $29.99/month</li>
            <li>Enterprise: Contact us for pricing</li>
        </ul>
    </div>
</template>

<script>
export default {
    name: 'Pricing'
}
</script>

<style scoped>
.pricing {
    padding: 20px;
}

.pricing ul {
    list-style-type: none;
    padding-left: 0;
}

.pricing li {
    margin: 10px 0;
}
</style>
