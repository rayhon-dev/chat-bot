document.addEventListener('DOMContentLoaded', function () {
    const providerField = document.getElementById('id_llm_provider');
    let modelField = document.getElementById('id_llm_model');
    if (!providerField || !modelField) return;

    const MODEL_OPTIONS = {
        openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini', 'o3-mini'],
        gemini: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
        anthropic: ['claude-opus-4-6', 'claude-sonnet-5', 'claude-haiku-4-5'],
        deepseek: ['deepseek-v4-flash', 'deepseek-v4', 'deepseek-coder'],
    };

    function buildSelect(provider, currentValue) {
        const options = MODEL_OPTIONS[provider] || [];
        const select = document.createElement('select');
        select.name = modelField.name;
        select.id = modelField.id;
        select.className = modelField.className;

        const empty = document.createElement('option');
        empty.value = '';
        empty.textContent = '---------';
        select.appendChild(empty);

        options.forEach(function (model) {
            const opt = document.createElement('option');
            opt.value = model;
            opt.textContent = model;
            if (model === currentValue) opt.selected = true;
            select.appendChild(opt);
        });

        modelField.replaceWith(select);
        modelField = select;
    }

    providerField.addEventListener('change', function () {
        buildSelect(providerField.value, modelField.value);
    });

    buildSelect(providerField.value, modelField.value);
});