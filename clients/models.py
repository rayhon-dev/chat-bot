from django.db import models
from django.utils.text import slugify
import secrets


class Client(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Bot(models.Model):
    class LLMProvider(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        GEMINI = "gemini", "Gemini"
        ANTHROPIC = "anthropic", "Anthropic (Claude)"
        DEEPSEEK = "deepseek", "DeepSeek"

    class ApiKeySource(models.TextChoices):
        PLATFORM = "platform", "Platforma key"
        CLIENT = "client", "Client o'z key'ini kiritadi"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bots")
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    telegram_enabled = models.BooleanField(default=False)
    telegram_bot_token = models.CharField(max_length=255, blank=True, null=True)
    telegram_group_mode = models.BooleanField(default=False)
    relevance_criteria = models.TextField(
        blank=True,
        help_text="Guruhda qaysi mavzudagi savollarga javob berish kerakligini tavsiflang. Masalan: 'mahsulot narxi, yetkazib berish, mavjudligi haqida savollar'"
    )
    website_enabled = models.BooleanField(default=False)
    api_key = models.CharField(max_length=255, unique=True, blank=True, null=True)
    uses_rag = models.BooleanField(default=True)
    api_key_source = models.CharField(max_length=20, choices=ApiKeySource.choices, default=ApiKeySource.PLATFORM)
    client_api_key = models.CharField(max_length=255, blank=True, null=True)
    llm_provider = models.CharField(max_length=20, choices=LLMProvider.choices, default=LLMProvider.OPENAI)
    llm_model = models.CharField(max_length=100, blank=True, null=True)
    embedding_model = models.CharField(max_length=100, blank=True, null=True)
    milvus_collection_name = models.CharField(max_length=255, blank=True, null=True)
    temperature = models.FloatField(default=0.7)
    system_prompt = models.TextField(blank=True)
    welcome_message = models.CharField(max_length=500, blank=True)
    fallback_message = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.client.name})"


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.website_enabled and not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)