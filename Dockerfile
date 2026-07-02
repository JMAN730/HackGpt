FROM kalilinux/kali-rolling

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Update and install basic tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    portaudio19-dev \
    git \
    curl \
    wget \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /hackgpt

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install -r requirements.txt --break-system-packages

# Copy the rest of the application
COPY . .

# Run installation script
RUN chmod +x install.sh && ./install.sh

# Create reports directory
RUN mkdir -p /reports && chmod 755 /reports

# Expose web dashboard port
EXPOSE 5000

# Set entry point
ENTRYPOINT ["python3", "advance_hackgpt.py"]
