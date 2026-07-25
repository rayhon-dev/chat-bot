(function ($) {
    "use strict";

    var MODEL_CHOICES = {
        openai: ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o4-mini"],
        deepseek: ["deepseek-chat", "deepseek-reasoner"],
        gemini: ["gemini-2.5-pro", "gemini-2.5-flash"],
        anthropic: ["claude-opus-5", "claude-sonnet-5", "claude-fable-5", "claude-haiku-4-5-20251001"]
    };

    $(function () {
        var $provider = $("#id_llm_provider");
        var $model = $("#id_llm_model");

        if (!$provider.length || !$model.length) {
            return;
        }

        var $datalist = $('<datalist id="llm_model_choices"></datalist>');
        $model.after($datalist).attr("list", "llm_model_choices");

        function updateChoices() {
            var choices = MODEL_CHOICES[$provider.val()] || [];
            $datalist.empty();
            choices.forEach(function (choice) {
                $datalist.append($("<option>").val(choice));
            });
        }

        $provider.on("change", updateChoices);
        updateChoices();
    });
})(django.jQuery);
